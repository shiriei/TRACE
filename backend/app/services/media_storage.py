"""TRACE Local Media Storage Service.

Handles safe filesystem operations for media attachments:
- Generated, unpredictable filenames (UUID-based).
- Path traversal prevention and strict directory sandboxing.
- Streaming uploads with configurable max file size enforcement.
- Magic bytes / content header verification for photos and audio.
- Cleanup of partial uploads upon failure.
- Safe deletion preventing deletion outside the configured media root.
"""
import logging
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger("trace.services.media_storage")


class MediaStorageError(Exception):
    """Base exception for media storage operations."""
    pass


class UnsupportedMediaTypeError(MediaStorageError):
    """Raised when file content or MIME type is not a supported photo or audio format."""
    pass


class FileTooLargeError(MediaStorageError):
    """Raised when uploaded file exceeds maximum allowed bytes."""
    pass


class PathTraversalError(MediaStorageError):
    """Raised when a filename or path attempts directory escape."""
    pass


class AttachmentNotFoundError(MediaStorageError):
    """Raised when an attachment file is not found."""
    pass


# Magic byte signatures and content sniffers
def sniff_media_type(
    header: bytes,
    declared_mime: Optional[str] = None,
    declared_filename: Optional[str] = None,
) -> Tuple[str, str, str]:
    """Inspect magic bytes header and determine media type, canonical mime, and safe extension.

    Returns:
        Tuple of (media_type ['photo' | 'audio'], canonical_mime, extension)

    Raises:
        UnsupportedMediaTypeError: If content fails signature verification or is unsupported.
    """
    if len(header) < 4:
        raise UnsupportedMediaTypeError("File is empty or too small to verify content type.")

    # 1. Photo signatures
    # JPEG: FF D8 FF
    if header.startswith(b"\xff\xd8\xff"):
        return "photo", "image/jpeg", "jpg"

    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "photo", "image/png", "png"

    # GIF: GIF87a or GIF89a
    if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        return "photo", "image/gif", "gif"

    # WebP: RIFF .... WEBP
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "photo", "image/webp", "webp"

    # 2. Audio signatures
    # WAV: RIFF .... WAVE
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE":
        return "audio", "audio/wav", "wav"

    # Ogg: OggS
    if header.startswith(b"OggS"):
        return "audio", "audio/ogg", "ogg"

    # WebM Audio / Video container (EBML: 1A 45 DF A3)
    if header.startswith(b"\x1a\x45\xdf\xa3"):
        # Check declared mime to confirm audio
        if declared_mime and "audio" in declared_mime.lower():
            return "audio", "audio/webm", "webm"
        # Default webm upload in TRACE audio context
        return "audio", "audio/webm", "webm"

    # MP3 with ID3 tag: ID3
    if header.startswith(b"ID3"):
        return "audio", "audio/mpeg", "mp3"

    # MP3 raw frame sync: FF FB, FF F3, FF F2
    if len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0:
        return "audio", "audio/mpeg", "mp3"

    # M4A / AAC (MP4 ftyp container: ....ftyp)
    if len(header) >= 8 and header[4:8] == b"ftyp":
        return "audio", "audio/x-m4a", "m4a"

    # FLAC: fLaC
    if header.startswith(b"fLaC"):
        return "audio", "audio/flac", "flac"

    # Unsupported or binary mismatch
    raise UnsupportedMediaTypeError(
        f"Unsupported file format or invalid media signature. "
        f"Only standard photo formats (JPEG, PNG, WebP, GIF) and audio formats (MP3, WAV, OGG, WebM, M4A, FLAC) are permitted."
    )


class MediaStorageService:
    """Manages file storage, path isolation, and streaming I/O for media attachments."""

    def __init__(
        self,
        media_dir: Optional[str] = None,
        max_upload_size: Optional[int] = None,
    ):
        raw_dir = media_dir if media_dir is not None else settings.MEDIA_DIR
        self.base_dir = self._resolve_dir(raw_dir)
        self.max_upload_size = (
            max_upload_size if max_upload_size is not None else settings.MAX_UPLOAD_SIZE_BYTES
        )
        self._ensure_dir()

    @staticmethod
    def _resolve_dir(path_str: str) -> Path:
        p = Path(path_str)
        if not p.is_absolute():
            backend_dir = Path(__file__).resolve().parent.parent.parent
            p = (backend_dir / p).resolve()
        return p.resolve()

    def _ensure_dir(self) -> None:
        """Create media directory if it does not exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def resolve_safe_path(self, filename: str) -> Path:
        """Resolve a filename into a validated absolute path strictly within the media directory.

        Prevents directory traversal, path escape, and relative separators.
        """
        if not filename or not isinstance(filename, str):
            raise PathTraversalError("Invalid filename provided.")

        # Reject path separators and directory navigation symbols
        if "/" in filename or "\\" in filename or ".." in filename or "\x00" in filename:
            raise PathTraversalError(f"Potentially malicious filename rejected: '{filename}'")

        # Strip any accidental leading/trailing whitespace
        clean_name = filename.strip()
        if not clean_name or clean_name in (".", ".."):
            raise PathTraversalError("Invalid filename.")

        target = (self.base_dir / clean_name).resolve()

        # Strict containment check
        try:
            target.relative_to(self.base_dir)
        except ValueError:
            raise PathTraversalError(f"Path escape attempt detected for: '{filename}'")

        if target.parent != self.base_dir:
            raise PathTraversalError("Subdirectory nesting is not allowed in media storage.")

        return target

    def generate_stored_filename(self, extension: str) -> str:
        """Generate a unique, unpredictable filename with a sanitized extension."""
        clean_ext = extension.lstrip(".").lower().strip()
        # Keep extension alphanumeric
        clean_ext = "".join(c for c in clean_ext if c.isalnum())
        if not clean_ext:
            clean_ext = "bin"

        # Loop until unique (astronomically instant)
        while True:
            unique_name = f"{uuid.uuid4().hex}.{clean_ext}"
            candidate = self.base_dir / unique_name
            if not candidate.exists():
                return unique_name

    async def save_upload_stream(
        self,
        upload_file: UploadFile,
    ) -> Tuple[str, str, str, int, Optional[str]]:
        """Stream an uploaded file to disk with strict size, signature, and traversal safeguards.

        Returns:
            Tuple of:
            (stored_filename, media_type, verified_mime, file_size_bytes, original_filename)

        Raises:
            UnsupportedMediaTypeError: If content signature is unsupported or invalid.
            FileTooLargeError: If upload exceeds max_upload_size.
            MediaStorageError: On I/O or stream error.
        """
        original_filename = upload_file.filename
        declared_mime = upload_file.content_type

        # 1. Read initial chunk to sniff magic bytes without buffering entire file
        chunk_size = 64 * 1024  # 64 KB
        first_chunk = await upload_file.read(chunk_size)
        if not first_chunk:
            raise UnsupportedMediaTypeError("Uploaded file is empty.")

        # Sniff media type, canonical mime, and safe extension
        media_type, canonical_mime, ext = sniff_media_type(
            header=first_chunk,
            declared_mime=declared_mime,
            declared_filename=original_filename,
        )

        # 2. Generate safe stored filename
        stored_filename = self.generate_stored_filename(ext)
        dest_path = self.resolve_safe_path(stored_filename)

        bytes_written = 0
        file_handle = None

        try:
            file_handle = open(dest_path, "wb")
            # Write the initial sniffed chunk
            bytes_written += len(first_chunk)
            if bytes_written > self.max_upload_size:
                raise FileTooLargeError(
                    f"Uploaded file exceeds maximum limit of {self.max_upload_size} bytes."
                )
            file_handle.write(first_chunk)

            # 3. Stream remaining chunks
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > self.max_upload_size:
                    raise FileTooLargeError(
                        f"Uploaded file exceeds maximum limit of {self.max_upload_size} bytes."
                    )
                file_handle.write(chunk)

            file_handle.flush()
            os.fsync(file_handle.fileno())

        except Exception as exc:
            # Safe cleanup of partial upload
            if file_handle and not file_handle.closed:
                file_handle.close()
            if dest_path.exists():
                try:
                    dest_path.unlink()
                    logger.debug("Cleaned up partial upload: %s", dest_path)
                except Exception as cleanup_err:
                    logger.warning("Failed to clean up partial file %s: %s", dest_path, cleanup_err)
            raise exc
        finally:
            if file_handle and not file_handle.closed:
                file_handle.close()

        logger.info(
            "Saved media attachment '%s' (%s, %d bytes) as '%s'",
            original_filename,
            canonical_mime,
            bytes_written,
            stored_filename,
        )

        return (
            stored_filename,
            media_type,
            canonical_mime,
            bytes_written,
            original_filename,
        )

    def get_file_path(self, stored_filename: str) -> Path:
        """Retrieve and validate the path to an existing stored file."""
        target = self.resolve_safe_path(stored_filename)
        if not target.exists() or not target.is_file():
            raise AttachmentNotFoundError(f"Media file '{stored_filename}' not found on disk.")
        return target

    def delete_file(self, stored_filename: str) -> bool:
        """Safely delete a stored file from the media directory.

        Guarantees deletion only occurs strictly inside base_dir.
        """
        try:
            target = self.resolve_safe_path(stored_filename)
        except PathTraversalError as err:
            logger.warning("Rejected delete request with unsafe filename: %s", err)
            return False

        if target.exists() and target.is_file():
            try:
                target.unlink()
                logger.info("Deleted stored media file: %s", stored_filename)
                return True
            except Exception as err:
                logger.error("Failed to delete media file %s: %s", target, err)
                raise MediaStorageError(f"Failed to delete stored file: {err}") from err
        return False


# Default storage singleton
default_media_storage = MediaStorageService()


def get_media_storage() -> MediaStorageService:
    """FastAPI dependency provider for MediaStorageService."""
    return default_media_storage
