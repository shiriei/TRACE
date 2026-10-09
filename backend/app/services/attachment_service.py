"""TRACE Attachment Service.

Coordinates validation, media storage, and database persistence for attachments.
"""
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import uuid

from fastapi import Depends, UploadFile

from app.models.attachment import AttachmentModel
from app.repositories.attachment_repository import (
    AttachmentRepository,
    get_attachment_repository,
)
from app.repositories.trace_repository import (
    TraceRepository,
    get_trace_repository,
)
from app.services.media_storage import (
    AttachmentNotFoundError,
    FileTooLargeError,
    MediaStorageError,
    MediaStorageService,
    PathTraversalError,
    UnsupportedMediaTypeError,
    get_media_storage,
)

logger = logging.getLogger("trace.services.attachment")


class TraceNotFoundError(Exception):
    """Raised when the associated trace does not exist."""
    pass


class AttachmentService:
    """Coordinates business logic and storage for trace media attachments."""

    def __init__(
        self,
        trace_repository: Optional[TraceRepository] = None,
        attachment_repository: Optional[AttachmentRepository] = None,
        media_storage: Optional[MediaStorageService] = None,
    ):
        self._trace_repo = trace_repository
        self._attachment_repo = attachment_repository
        self._storage = media_storage

    @property
    def trace_repo(self) -> TraceRepository:
        return self._trace_repo or get_trace_repository()

    @property
    def attachment_repo(self) -> AttachmentRepository:
        return self._attachment_repo or get_attachment_repository()

    @property
    def storage(self) -> MediaStorageService:
        return self._storage or get_media_storage()

    async def upload_attachment(
        self,
        trace_id: str,
        upload_file: UploadFile,
    ) -> AttachmentModel:
        """Process and persist a media file attachment for an existing trace.

        1. Validates trace existence.
        2. Streams file to local storage under unpredictable filename.
        3. Enforces size limit, file signature, and directory sandboxing.
        4. Saves attachment metadata to SQLite.
        """
        # Step 1: Ensure trace exists
        trace = self.trace_repo.get_by_id(trace_id)
        if not trace:
            raise TraceNotFoundError(f"Trace '{trace_id}' not found.")

        # Step 2: Stream upload to disk with security and signature checks
        (
            stored_filename,
            media_type,
            canonical_mime,
            file_size_bytes,
            original_filename,
        ) = await self.storage.save_upload_stream(upload_file)

        # Step 3: Persist attachment metadata record
        attachment_id = f"attach-{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()

        attachment = AttachmentModel(
            id=attachment_id,
            trace_id=trace_id,
            media_type=media_type,
            stored_filename=stored_filename,
            original_filename=original_filename,
            mime_type=canonical_mime,
            file_size_bytes=file_size_bytes,
            created_at=created_at,
        )

        try:
            return self.attachment_repo.create(attachment)
        except Exception as exc:
            # Clean up stored file if database insertion fails
            logger.error(
                "Failed to save attachment metadata for %s. Cleaning up file %s: %s",
                attachment_id,
                stored_filename,
                exc,
            )
            self.storage.delete_file(stored_filename)
            raise exc

    def list_attachments(self, trace_id: str) -> List[AttachmentModel]:
        """List all attachments associated with a trace."""
        trace = self.trace_repo.get_by_id(trace_id)
        if not trace:
            raise TraceNotFoundError(f"Trace '{trace_id}' not found.")
        return self.attachment_repo.get_by_trace_id(trace_id)

    def get_attachment(self, trace_id: str, attachment_id: str) -> Optional[AttachmentModel]:
        """Retrieve attachment metadata verifying trace association."""
        attachment = self.attachment_repo.get_by_id(attachment_id)
        if not attachment or attachment.trace_id != trace_id:
            return None
        return attachment

    def get_attachment_content(self, trace_id: str, attachment_id: str) -> Tuple[Path, AttachmentModel]:
        """Retrieve on-disk file path and metadata for streaming attachment bytes."""
        attachment = self.get_attachment(trace_id, attachment_id)
        if not attachment:
            raise AttachmentNotFoundError(f"Attachment '{attachment_id}' not found for trace '{trace_id}'.")
        path = self.storage.get_file_path(attachment.stored_filename)
        return path, attachment

    def delete_attachment(self, trace_id: str, attachment_id: str) -> bool:
        """Safely delete an attachment record and its on-disk media file."""
        attachment = self.get_attachment(trace_id, attachment_id)
        if not attachment:
            return False

        # First safely delete stored file on disk
        self.storage.delete_file(attachment.stored_filename)

        # Delete database metadata
        return self.attachment_repo.delete(attachment_id)


default_attachment_service = AttachmentService()


def get_attachment_service(
    trace_repo: TraceRepository = Depends(get_trace_repository),
    attachment_repo: AttachmentRepository = Depends(get_attachment_repository),
    storage: MediaStorageService = Depends(get_media_storage),
) -> AttachmentService:
    """FastAPI dependency provider for AttachmentService."""
    return AttachmentService(
        trace_repository=trace_repo,
        attachment_repository=attachment_repo,
        media_storage=storage,
    )
