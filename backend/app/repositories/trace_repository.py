"""TRACE Data Access Layer for Traces."""
import json
import logging
import sqlite3
from typing import List, Optional

from app.db.database import SQLiteDatabase, get_db
from app.models.trace import TraceModel

logger = logging.getLogger("trace.repositories.trace")


def _row_to_model(row: sqlite3.Row) -> TraceModel:
    tags_raw = row["tags"]
    tags: List[str] = []
    if tags_raw:
        try:
            parsed = json.loads(tags_raw)
            if isinstance(parsed, list):
                tags = [str(t) for t in parsed]
        except (json.JSONDecodeError, TypeError):
            tags = []

    lat_val = row["latitude"]
    lng_val = row["longitude"]
    latitude = float(lat_val) if lat_val is not None else None
    longitude = float(lng_val) if lng_val is not None else None

    # Handle location_mode from row or infer for older schemas
    location_mode = "unplaced"
    if "location_mode" in row.keys() and row["location_mode"]:
        location_mode = str(row["location_mode"])
    elif latitude is not None and longitude is not None:
        location_mode = "manual"

    return TraceModel(
        id=str(row["id"]),
        observation=str(row["observation"]),
        category=str(row["category"]),
        title=str(row["title"]),
        summary=str(row["summary"]),
        tags=tags,
        sensory_type=str(row["sensory_type"]),
        confidence=float(row["confidence"]),
        latitude=latitude,
        longitude=longitude,
        location_mode=location_mode,
        created_at=str(row["created_at"]),
        photo_path=row["photo_path"],
        audio_path=row["audio_path"],
    )


class TraceRepository:
    """Repository handling SQL persistence and querying for Trace entities."""

    def __init__(self, database: Optional[SQLiteDatabase] = None):
        self._db = database

    @property
    def db(self) -> SQLiteDatabase:
        return self._db or get_db()

    def create(self, trace: TraceModel) -> TraceModel:
        """Insert a new trace record into SQLite."""
        tags_json = json.dumps(trace.tags)
        sql = """
            INSERT INTO traces (
                id, observation, category, title, summary, tags,
                sensory_type, confidence, latitude, longitude, location_mode,
                created_at, photo_path, audio_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.db.get_connection() as conn:
            conn.execute(
                sql,
                (
                    trace.id,
                    trace.observation,
                    trace.category,
                    trace.title,
                    trace.summary,
                    tags_json,
                    trace.sensory_type,
                    trace.confidence,
                    trace.latitude,
                    trace.longitude,
                    trace.location_mode,
                    trace.created_at,
                    trace.photo_path,
                    trace.audio_path,
                ),
            )
        return trace

    def get_by_id(self, trace_id: str) -> Optional[TraceModel]:
        """Fetch a single trace by its ID."""
        sql = "SELECT * FROM traces WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (trace_id,))
            row = cursor.fetchone()
            if row:
                return _row_to_model(row)
        return None

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        category: Optional[str] = None,
    ) -> List[TraceModel]:
        """Fetch all traces ordered by creation time descending."""
        with self.db.get_connection() as conn:
            if category:
                sql = """
                    SELECT * FROM traces
                    WHERE category = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """
                cursor = conn.execute(sql, (category, limit, offset))
            else:
                sql = """
                    SELECT * FROM traces
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """
                cursor = conn.execute(sql, (limit, offset))
            rows = cursor.fetchall()
            return [_row_to_model(row) for row in rows]

    def update_ai_metadata(
        self,
        trace_id: str,
        category: str,
        title: str,
        summary: str,
        tags: List[str],
        sensory_type: str,
        confidence: float,
    ) -> Optional[TraceModel]:
        """Update trace classification and AI fields after inference."""
        tags_json = json.dumps(tags)
        sql = """
            UPDATE traces
            SET category = ?,
                title = ?,
                summary = ?,
                tags = ?,
                sensory_type = ?,
                confidence = ?
            WHERE id = ?
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                sql,
                (
                    category,
                    title,
                    summary,
                    tags_json,
                    sensory_type,
                    confidence,
                    trace_id,
                ),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_by_id(trace_id)

    def delete(self, trace_id: str) -> bool:
        """Delete a trace by ID. Returns True if deleted, False if not found."""
        sql = "DELETE FROM traces WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (trace_id,))
            return cursor.rowcount > 0

    def count(self) -> int:
        """Return total count of recorded traces."""
        sql = "SELECT COUNT(*) FROM traces"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql)
            row = cursor.fetchone()
            return int(row[0]) if row else 0


default_trace_repository = TraceRepository()


def get_trace_repository() -> TraceRepository:
    """FastAPI dependency provider for TraceRepository."""
    return default_trace_repository
