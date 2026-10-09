"""TRACE Data Access Layer for Attachments."""
import logging
import sqlite3
from typing import List, Optional

from app.db.database import SQLiteDatabase, get_db
from app.models.attachment import AttachmentModel

logger = logging.getLogger("trace.repositories.attachment")


def _row_to_attachment(row: sqlite3.Row) -> AttachmentModel:
    return AttachmentModel(
        id=str(row["id"]),
        trace_id=str(row["trace_id"]),
        media_type=str(row["media_type"]),
        stored_filename=str(row["stored_filename"]),
        original_filename=str(row["original_filename"]) if row["original_filename"] is not None else None,
        mime_type=str(row["mime_type"]),
        file_size_bytes=int(row["file_size_bytes"]),
        created_at=str(row["created_at"]),
    )


class AttachmentRepository:
    """Repository handling SQL persistence for Attachment entities."""

    def __init__(self, database: Optional[SQLiteDatabase] = None):
        self._db = database

    @property
    def db(self) -> SQLiteDatabase:
        return self._db or get_db()

    def create(self, attachment: AttachmentModel) -> AttachmentModel:
        """Insert a new attachment record into SQLite."""
        sql = """
            INSERT INTO attachments (
                id, trace_id, media_type, stored_filename, original_filename,
                mime_type, file_size_bytes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.db.get_connection() as conn:
            conn.execute(
                sql,
                (
                    attachment.id,
                    attachment.trace_id,
                    attachment.media_type,
                    attachment.stored_filename,
                    attachment.original_filename,
                    attachment.mime_type,
                    attachment.file_size_bytes,
                    attachment.created_at,
                ),
            )
        return attachment

    def get_by_id(self, attachment_id: str) -> Optional[AttachmentModel]:
        """Fetch a single attachment by ID."""
        sql = "SELECT * FROM attachments WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (attachment_id,))
            row = cursor.fetchone()
            if row:
                return _row_to_attachment(row)
        return None

    def get_by_trace_id(self, trace_id: str) -> List[AttachmentModel]:
        """Fetch all attachments associated with a specific trace ordered chronologically."""
        sql = "SELECT * FROM attachments WHERE trace_id = ? ORDER BY created_at ASC"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (trace_id,))
            rows = cursor.fetchall()
            return [_row_to_attachment(row) for row in rows]

    def delete(self, attachment_id: str) -> bool:
        """Delete an attachment record by ID. Returns True if deleted, False otherwise."""
        sql = "DELETE FROM attachments WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (attachment_id,))
            return cursor.rowcount > 0

    def delete_by_trace_id(self, trace_id: str) -> int:
        """Delete all attachment records associated with a trace ID."""
        sql = "DELETE FROM attachments WHERE trace_id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (trace_id,))
            return cursor.rowcount

    def count_other_references(self, stored_filename: str, exclude_trace_id: str) -> int:
        """Count how many other traces reference the same stored filename."""
        sql = "SELECT COUNT(*) FROM attachments WHERE stored_filename = ? AND trace_id != ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (stored_filename, exclude_trace_id))
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    def count(self) -> int:
        """Return total count of stored attachments."""
        sql = "SELECT COUNT(*) FROM attachments"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql)
            row = cursor.fetchone()
            return int(row[0]) if row else 0


default_attachment_repository = AttachmentRepository()


def get_attachment_repository() -> AttachmentRepository:
    """FastAPI dependency provider for AttachmentRepository."""
    return default_attachment_repository
