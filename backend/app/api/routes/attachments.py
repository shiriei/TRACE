"""TRACE Attachments API Routes."""
import logging
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from app.schemas.attachment import (
    AttachmentDeleteResponse,
    AttachmentResponse,
)
from app.services.attachment_service import (
    AttachmentNotFoundError,
    AttachmentService,
    FileTooLargeError,
    PathTraversalError,
    TraceNotFoundError,
    UnsupportedMediaTypeError,
    get_attachment_service,
)

logger = logging.getLogger("trace.api.attachments")

router = APIRouter()


@router.post(
    "/{trace_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload media attachment for a trace",
    description="Streams and persists a photo or audio file attached to a specific trace.",
)
async def upload_attachment(
    trace_id: str,
    file: UploadFile = File(..., description="Multipart photo or audio file"),
    service: AttachmentService = Depends(get_attachment_service),
):
    """Upload photo or audio attachment for an existing trace."""
    try:
        return await service.upload_attachment(trace_id=trace_id, upload_file=file)
    except TraceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except UnsupportedMediaTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        )
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        )
    except PathTraversalError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error uploading attachment for trace %s: %s", trace_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store attachment.",
        )


@router.get(
    "/{trace_id}/attachments",
    response_model=List[AttachmentResponse],
    summary="List attachments for a trace",
    description="Retrieves all photo and audio attachments linked to the specified trace.",
)
async def list_attachments(
    trace_id: str,
    service: AttachmentService = Depends(get_attachment_service),
):
    """List all attachments for a trace."""
    try:
        return service.list_attachments(trace_id=trace_id)
    except TraceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "/{trace_id}/attachments/{attachment_id}",
    response_model=AttachmentResponse,
    summary="Retrieve attachment metadata",
    description="Returns metadata for a specific attachment belonging to a trace.",
)
async def get_attachment_metadata(
    trace_id: str,
    attachment_id: str,
    service: AttachmentService = Depends(get_attachment_service),
):
    """Get metadata for a single attachment."""
    attachment = service.get_attachment(trace_id=trace_id, attachment_id=attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment '{attachment_id}' not found for trace '{trace_id}'.",
        )
    return attachment


@router.get(
    "/{trace_id}/attachments/{attachment_id}/content",
    summary="Stream attachment content",
    description="Streams the binary content of the stored media file.",
)
async def get_attachment_content(
    trace_id: str,
    attachment_id: str,
    service: AttachmentService = Depends(get_attachment_service),
):
    """Retrieve and stream media content."""
    try:
        file_path, attachment = service.get_attachment_content(
            trace_id=trace_id,
            attachment_id=attachment_id,
        )
    except AttachmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return FileResponse(
        path=str(file_path),
        media_type=attachment.mime_type,
        filename=attachment.original_filename or attachment.stored_filename,
    )


@router.delete(
    "/{trace_id}/attachments/{attachment_id}",
    response_model=AttachmentDeleteResponse,
    summary="Delete an attachment",
    description="Permanently deletes the stored media file and its attachment metadata.",
)
async def delete_attachment(
    trace_id: str,
    attachment_id: str,
    service: AttachmentService = Depends(get_attachment_service),
):
    """Delete an attachment and its stored file."""
    deleted = service.delete_attachment(trace_id=trace_id, attachment_id=attachment_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment '{attachment_id}' not found for trace '{trace_id}'.",
        )
    return AttachmentDeleteResponse(
        message="Attachment deleted successfully",
        id=attachment_id,
        trace_id=trace_id,
    )
