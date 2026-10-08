"""TRACE Service coordinating Trace persistence and local AI interpretation."""
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends

from app.ai.schemas import TraceAIResult
from app.ai.service import TraceAIService, ai_service
from app.models.trace import TraceModel
from app.repositories.trace_repository import (
    TraceRepository,
    get_trace_repository,
)
from app.schemas.trace import TraceCreate

logger = logging.getLogger("trace.services.trace")


class TraceService:
    """Coordinates Trace persistence and local AI interpretation."""

    def __init__(
        self,
        repository: Optional[TraceRepository] = None,
        ai_svc: Optional[TraceAIService] = None,
    ):
        self._repository = repository
        self.ai_svc = ai_svc or ai_service

    @property
    def repository(self) -> TraceRepository:
        return self._repository or get_trace_repository()

    async def create_trace(self, data: TraceCreate) -> TraceModel:
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
        """Delete a trace by ID."""
        return self.repository.delete(trace_id)

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
) -> TraceService:
    """FastAPI dependency provider for TraceService."""
    return TraceService(repository=repository)
