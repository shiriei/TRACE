"""TRACE Pydantic Schemas for Attachment API Payloads and Responses."""
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

MediaType = Literal["photo", "audio"]


class AttachmentResponse(BaseModel):
    """Structured response representation of an attachment."""

    id: str = Field(..., description="Unique attachment identifier.")
    trace_id: str = Field(..., description="Identifier of the associated trace.")
    media_type: MediaType = Field(..., description="Media type: 'photo' or 'audio'.")
    stored_filename: str = Field(..., description="Generated, unpredictable stored filename.")
    original_filename: Optional[str] = Field(
        default=None,
        description="Original client filename if available.",
    )
    mime_type: str = Field(..., description="Verified MIME content type.")
    file_size_bytes: int = Field(..., description="File size in bytes.")
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")

    model_config = ConfigDict(from_attributes=True)


class AttachmentDeleteResponse(BaseModel):
    """Response returned upon attachment deletion."""

    message: str = Field(..., description="Confirmation message.")
    id: str = Field(..., description="Identifier of the deleted attachment.")
    trace_id: str = Field(..., description="Identifier of the associated trace.")
