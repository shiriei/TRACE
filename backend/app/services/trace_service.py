"""TRACE Service coordinating Trace persistence and local AI interpretation."""
import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends

from app.ai.schemas import TraceAIResult
from app.ai.service import TraceAIService, ai_service
from app.models.trace import TraceModel
from app.repositories.attachment_repository import (
    AttachmentRepository,
    get_attachment_repository,
)
from app.repositories.trace_repository import (
    TraceRepository,
    get_trace_repository,
)
from app.schemas.trace import TraceCreate
from app.services.media_storage import (
    MediaStorageService,
    get_media_storage,
)

logger = logging.getLogger("trace.services.trace")

_IN_FLIGHT: dict[str, asyncio.Future[TraceModel]] = {}
_RECENT_COMPLETED: dict[str, tuple[float, TraceModel]] = {}
_DEDUP_WINDOW_SECONDS: float = 3.0


class TraceService:
    """Coordinates Trace persistence and local AI interpretation."""

    def __init__(
        self,
        repository: Optional[TraceRepository] = None,
        attachment_repository: Optional[AttachmentRepository] = None,
        media_storage: Optional[MediaStorageService] = None,
        ai_svc: Optional[TraceAIService] = None,
    ):
        self._repository = repository
        self._attachment_repository = attachment_repository
        self._media_storage = media_storage
        self.ai_svc = ai_svc or ai_service

    @property
    def repository(self) -> TraceRepository:
        return self._repository or get_trace_repository()

    @property
    def attachment_repo(self) -> AttachmentRepository:
        return self._attachment_repository or get_attachment_repository()

    @property
    def media_storage(self) -> MediaStorageService:
        return self._media_storage or get_media_storage()

    def _make_dedup_key(self, data: TraceCreate) -> str:
        obs = data.observation.strip()
        lat = round(data.latitude, 6) if data.latitude is not None else None
        lng = round(data.longitude, 6) if data.longitude is not None else None
        mode = data.location_mode or ("unplaced" if lat is None else "manual")
        return f"{obs}|{lat}|{lng}|{mode}"

    async def create_trace(self, data: TraceCreate) -> TraceModel:
        """Create a new trace with duplicate submission protection."""
        now = time.monotonic()
        # Clean expired completed entries
        expired_keys = [k for k, v in _RECENT_COMPLETED.items() if now - v[0] >= _DEDUP_WINDOW_SECONDS]
        for k in expired_keys:
            _RECENT_COMPLETED.pop(k, None)

        dedup_key = self._make_dedup_key(data)

        # 1. If an identical trace was just completed within the deduplication window, return it
        if dedup_key in _RECENT_COMPLETED:
            ts, cached_trace = _RECENT_COMPLETED[dedup_key]
            if self.repository.get_by_id(cached_trace.id) is not None:
                logger.info("Suppressed duplicate trace submission for key: %s", dedup_key)
                return cached_trace
            _RECENT_COMPLETED.pop(dedup_key, None)

        # 2. If an identical trace is currently in-flight, await its completion
        if dedup_key in _IN_FLIGHT:
            logger.info("Awaiting in-flight duplicate submission for key: %s", dedup_key)
            try:
                return await _IN_FLIGHT[dedup_key]
            except Exception:
                # If concurrent task failed, proceed to try fresh
                pass

        loop = asyncio.get_running_loop()
        future: asyncio.Future[TraceModel] = loop.create_future()
        _IN_FLIGHT[dedup_key] = future

        try:
            created = await self._execute_create_trace(data)
            if not future.done():
                future.set_result(created)
            _RECENT_COMPLETED[dedup_key] = (time.monotonic(), created)
            return created
        except Exception as exc:
            if not future.done():
                future.set_exception(exc)
                try:
                    future.exception()
                except Exception:
                    pass
            raise
        finally:
            _IN_FLIGHT.pop(dedup_key, None)

    async def _execute_create_trace(self, data: TraceCreate) -> TraceModel:
        """Create a new trace with persistent observation and AI classification.

        Lifecycle:
        1. Save observation with baseline/fallback metadata.
        2. Call existing AI interpretation service.
        3. Save returned category/title/summary/tags/sensory_type/confidence with the trace.
        If LM Studio is unavailable, trace creation still succeeds.
        """
        trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()

        # Step 1: Save the observation into persistent database
        initial_title = data.title or self._generate_fallback_title(data.observation)
        initial_category = data.category or "Personal"
        initial_summary = data.summary or data.observation
        initial_tags = data.tags if data.tags is not None else []
        initial_sensory = data.sensory_type or "visual"
        initial_confidence = 0.0

        trace = TraceModel(
            id=trace_id,
            observation=data.observation,
            category=initial_category,
            title=initial_title,
            summary=initial_summary,
            tags=initial_tags,
            sensory_type=initial_sensory,
            confidence=initial_confidence,
            latitude=data.latitude,
            longitude=data.longitude,
            location_mode=data.location_mode or "unplaced",
            created_at=created_at,
            photo_path=data.photo_path,
            audio_path=data.audio_path,
        )

        saved_trace = self.repository.create(trace)

        # Step 2: Call the existing AI interpretation service
        try:
            ai_result: TraceAIResult = await self.ai_svc.interpret_observation(data.observation)

            # Step 3: Save returned category/title/summary/tags/sensory_type/confidence
            updated_trace = self.repository.update_ai_metadata(
                trace_id=trace_id,
                category=data.category or ai_result.category,
                title=data.title or ai_result.title,
                summary=data.summary or ai_result.summary,
                tags=data.tags if data.tags is not None else ai_result.tags,
                sensory_type=data.sensory_type or ai_result.sensory_type,
                confidence=ai_result.confidence,
            )
            if updated_trace:
                return updated_trace
        except Exception as exc:
            logger.warning(
                "Local AI interpretation unavailable or failed for trace %s: %s. Trace retained with fallback metadata.",
                trace_id,
                exc,
            )

        # Trace remains successfully saved if LM Studio was unavailable
        return saved_trace

    def get_trace(self, trace_id: str) -> Optional[TraceModel]:
        """Retrieve a single trace by ID."""
        return self.repository.get_by_id(trace_id)

    def list_traces(
        self,
        limit: int = 100,
        offset: int = 0,
        category: Optional[str] = None,
    ) -> List[TraceModel]:
        """Retrieve recorded traces ordered by creation time descending."""
        return self.repository.get_all(limit=limit, offset=offset, category=category)

    def delete_trace(self, trace_id: str) -> bool:
        """Delete a trace by ID, safely cleaning up all associated attachment files and metadata.

        Guarantees:
        - Only deletes files strictly belonging to this trace (checks if shared).
        - Prevents directory traversal through media_storage.resolve_safe_path.
        - If filesystem cleanup fails, raises an error so trace is preserved.
        - Foreign keys and attachment records deleted safely.
        - Unrelated traces remain unaffected.
        """
        trace = self.repository.get_by_id(trace_id)
        if not trace:
            return False

        # 1. Clean up associated attachment files from media storage
        attachments = self.attachment_repo.get_by_trace_id(trace_id)
        for att in attachments:
            other_refs = self.attachment_repo.count_other_references(att.stored_filename, trace_id)
            if other_refs == 0:
                try:
                    self.media_storage.delete_file(att.stored_filename)
                except Exception as exc:
                    logger.error(
                        "Failed to delete stored file %s for attachment %s: %s",
                        att.stored_filename,
                        att.id,
                        exc,
                    )
                    from app.services.media_storage import MediaStorageError
                    raise MediaStorageError(f"Failed to delete media file for attachment {att.id}: {exc}") from exc
            else:
                logger.info(
                    "Skipping disk file deletion for %s as it is referenced by %d other trace(s).",
                    att.stored_filename,
                    other_refs,
                )

        # 2. Delete attachment metadata records
        self.attachment_repo.delete_by_trace_id(trace_id)

        # 3. Delete trace record
        deleted = self.repository.delete(trace_id)

        # 4. Clean up any in-memory dedup cache
        dedup_keys_to_remove = [
            k for k, (_, cached) in _RECENT_COMPLETED.items()
            if cached.id == trace_id
        ]
        for k in dedup_keys_to_remove:
            _RECENT_COMPLETED.pop(k, None)

        return deleted

    def cleanup_duplicate_creation_events(self) -> List[str]:
        """Conservatively clean up records proven to be duplicate submissions from the same creation event.

        Only removes records where:
        - Observation text matches exactly.
        - Location mode matches exactly.
        - Coordinates match exactly (or both None).
        - Created within 10 seconds of a preceding trace.
        Does NOT delete legitimate discoveries with matching titles or observations created separately.
        """
        all_traces = self.repository.get_all(limit=500, offset=0)
        # Sort chronologically
        sorted_traces = sorted(all_traces, key=lambda t: t.created_at)

        removed_ids: List[str] = []
        for i in range(len(sorted_traces)):
            curr = sorted_traces[i]
            if curr.id in removed_ids:
                continue

            for j in range(i):
                prev = sorted_traces[j]
                if prev.id in removed_ids:
                    continue

                if curr.observation.strip() == prev.observation.strip() and curr.location_mode == prev.location_mode:
                    coords_match = (
                        (curr.latitude == prev.latitude and curr.longitude == prev.longitude) or
                        (curr.latitude is None and prev.latitude is None)
                    )
                    if coords_match:
                        try:
                            t1 = datetime.fromisoformat(prev.created_at)
                            t2 = datetime.fromisoformat(curr.created_at)
                            diff = (t2 - t1).total_seconds()
                            if 0 < diff <= 10.0:
                                logger.info(
                                    "Cleaning proven duplicate trace %s (created %.2fs after %s)",
                                    curr.id,
                                    diff,
                                    prev.id,
                                )
                                self.delete_trace(curr.id)
                                removed_ids.append(curr.id)
                                break
                        except Exception as parse_err:
                            logger.warning("Failed to parse timestamps for duplicate comparison: %s", parse_err)

        return removed_ids

    @staticmethod
    def _generate_fallback_title(observation: str) -> str:
        """Derive a clean fallback title from observation text."""
        first_line = observation.strip().split("\n")[0].strip()
        if len(first_line) <= 50:
            return first_line
        cut = first_line[:50]
        last_space = cut.rfind(" ")
        if last_space > 15:
            return cut[:last_space].rstrip(".,;:- ")
        return cut.rstrip(".,;:- ")


default_trace_service = TraceService()


def get_trace_service(
    repository: TraceRepository = Depends(get_trace_repository),
    attachment_repository: AttachmentRepository = Depends(get_attachment_repository),
    media_storage: MediaStorageService = Depends(get_media_storage),
) -> TraceService:
    """FastAPI dependency provider for TraceService."""
    return TraceService(
        repository=repository,
        attachment_repository=attachment_repository,
        media_storage=media_storage,
    )

