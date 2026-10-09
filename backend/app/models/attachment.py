"""TRACE Domain and Persistence Model for Attachments."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AttachmentModel:
    """Domain model representing a persistent media attachment entity."""

    id: str
    trace_id: str
    media_type: str  # "photo" or "audio"
    stored_filename: str
    original_filename: Optional[str]
    mime_type: str
    file_size_bytes: int
    created_at: str
