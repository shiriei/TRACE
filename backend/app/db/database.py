"""TRACE SQLite Database Engine & Connection Management."""
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from app.core.config import settings

logger = logging.getLogger("trace.db")


class SQLiteDatabase:
    """Manages SQLite connection lifecycle, schema initialization, and PRAGMA settings."""

    def __init__(self, db_path: Optional[str] = None):
        self.raw_path = db_path if db_path is not None else settings.DATABASE_PATH
        self.db_path = self._resolve_path(self.raw_path)
        self._ensure_dir()
        self.init_db()

    @staticmethod
    def _resolve_path(path_str: str) -> str:
        if path_str == ":memory:" or path_str.startswith("file:"):
            return path_str
        p = Path(path_str)
        if not p.is_absolute():
            backend_dir = Path(__file__).resolve().parent.parent.parent
            p = (backend_dir / p).resolve()
        return str(p)

    def _ensure_dir(self) -> None:
        if self.db_path != ":memory:" and not self.db_path.startswith("file:"):
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def init_db(self) -> None:
        """Initialize database schema tables and indices if not present."""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    id TEXT PRIMARY KEY,
                    observation TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    sensory_type TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.0,
                    latitude REAL,
                    longitude REAL,
                    location_mode TEXT NOT NULL DEFAULT 'unplaced',
                    created_at TEXT NOT NULL,
                    photo_path TEXT,
                    audio_path TEXT
                );
                """
            )

            # Backwards compatibility check for existing databases
            cursor = conn.execute("PRAGMA table_info(traces);")
            columns = [row[1] for row in cursor.fetchall()]
            if "location_mode" not in columns:
                conn.execute(
                    "ALTER TABLE traces ADD COLUMN location_mode TEXT NOT NULL DEFAULT 'unplaced';"
                )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attachments (
                    id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    stored_filename TEXT NOT NULL,
                    original_filename TEXT,
                    mime_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (trace_id) REFERENCES traces(id) ON DELETE CASCADE
                );
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sticker_ownership (
                    id TEXT PRIMARY KEY,
                    sticker_id TEXT NOT NULL UNIQUE,
                    unlocked_at TEXT NOT NULL,
                    unlock_reason TEXT NOT NULL,
                    source TEXT NOT NULL
                );
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_reward_claims (
                    claim_date TEXT PRIMARY KEY,
                    sticker_id TEXT NOT NULL,
                    claimed_at TEXT NOT NULL
                );
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS milestone_claims (
                    milestone_id TEXT PRIMARY KEY,
                    streak_threshold INTEGER NOT NULL,
                    claimed_at TEXT NOT NULL,
                    pack_id TEXT NOT NULL
                );
                """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_created_at ON traces(created_at DESC);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_category ON traces(category);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_location_mode ON traces(location_mode);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_attachments_trace_id ON attachments(trace_id);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_attachments_created_at ON attachments(created_at DESC);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sticker_ownership_sticker_id ON sticker_ownership(sticker_id);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sticker_ownership_unlocked_at ON sticker_ownership(unlocked_at DESC);"
            )
            logger.info("TRACE SQLite database initialized at %s", self.db_path)


    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing a managed SQLite connection."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=15.0,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        if self.db_path != ":memory:" and not self.db_path.startswith("file:"):
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
            except Exception as e:
                logger.debug("PRAGMA journal_mode=WAL not applied: %s", e)
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# Default application database instance
db = SQLiteDatabase()


def get_db() -> SQLiteDatabase:
    """Dependency provider for SQLiteDatabase."""
    return db
