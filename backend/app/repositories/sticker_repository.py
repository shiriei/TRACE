"""TRACE Data Access Layer for Sticker Ownership."""
import logging
import sqlite3
from typing import List, Optional

from app.db.database import SQLiteDatabase, get_db
from app.models.sticker import StickerOwnershipModel

logger = logging.getLogger("trace.repositories.sticker")


def _row_to_ownership(row: sqlite3.Row) -> StickerOwnershipModel:
    return StickerOwnershipModel(
        id=str(row["id"]),
        sticker_id=str(row["sticker_id"]),
        unlocked_at=str(row["unlocked_at"]),
        unlock_reason=str(row["unlock_reason"]),
        source=str(row["source"]),
    )


class StickerRepository:
    """Repository handling SQL persistence for user sticker ownership records."""

    def __init__(self, database: Optional[SQLiteDatabase] = None):
        self._db = database

    @property
    def db(self) -> SQLiteDatabase:
        return self._db or get_db()

    def create(self, ownership: StickerOwnershipModel) -> StickerOwnershipModel:
        """Insert a new sticker ownership record into SQLite.
        
        Enforces UNIQUE(sticker_id) constraint from the database schema.
        """
        sql = """
            INSERT INTO sticker_ownership (
                id, sticker_id, unlocked_at, unlock_reason, source
            ) VALUES (?, ?, ?, ?, ?)
        """
        with self.db.get_connection() as conn:
            conn.execute(
                sql,
                (
                    ownership.id,
                    ownership.sticker_id,
                    ownership.unlocked_at,
                    ownership.unlock_reason,
                    ownership.source,
                ),
            )
        return ownership

    def get_by_id(self, ownership_id: str) -> Optional[StickerOwnershipModel]:
        """Fetch a single ownership record by its record ID."""
        sql = "SELECT * FROM sticker_ownership WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (ownership_id,))
            row = cursor.fetchone()
            if row:
                return _row_to_ownership(row)
        return None

    def get_by_sticker_id(self, sticker_id: str) -> Optional[StickerOwnershipModel]:
        """Fetch an ownership record for a specific sticker ID."""
        sql = "SELECT * FROM sticker_ownership WHERE sticker_id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (sticker_id,))
            row = cursor.fetchone()
            if row:
                return _row_to_ownership(row)
        return None

    def get_all(self) -> List[StickerOwnershipModel]:
        """Fetch all owned stickers ordered by unlock time descending."""
        sql = "SELECT * FROM sticker_ownership ORDER BY unlocked_at DESC"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql)
            rows = cursor.fetchall()
            return [_row_to_ownership(row) for row in rows]

    def delete(self, ownership_id: str) -> bool:
        """Delete an ownership record by record ID."""
        sql = "DELETE FROM sticker_ownership WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (ownership_id,))
            return cursor.rowcount > 0

    def delete_by_sticker_id(self, sticker_id: str) -> bool:
        """Delete an ownership record by sticker ID."""
        sql = "DELETE FROM sticker_ownership WHERE sticker_id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (sticker_id,))
            return cursor.rowcount > 0

    def count(self) -> int:
        """Return total count of owned stickers."""
        sql = "SELECT COUNT(*) FROM sticker_ownership"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql)
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    def get_daily_claim(self, claim_date: str) -> Optional[dict]:
        """Fetch daily reward claim for a specific calendar date (YYYY-MM-DD)."""
        sql = "SELECT claim_date, sticker_id, claimed_at FROM daily_reward_claims WHERE claim_date = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (claim_date,))
            row = cursor.fetchone()
            if row:
                return {
                    "claim_date": str(row[0]),
                    "sticker_id": str(row[1]),
                    "claimed_at": str(row[2]),
                }
        return None

    def record_daily_claim(self, claim_date: str, sticker_id: str, claimed_at: str) -> None:
        """Record that a daily sticker reward has been claimed for calendar date."""
        sql = "INSERT INTO daily_reward_claims (claim_date, sticker_id, claimed_at) VALUES (?, ?, ?)"
        with self.db.get_connection() as conn:
            conn.execute(sql, (claim_date, sticker_id, claimed_at))

    def get_milestone_claim(self, milestone_id: str) -> Optional[dict]:
        """Fetch milestone claim record by milestone ID."""
        sql = "SELECT milestone_id, streak_threshold, claimed_at, pack_id FROM milestone_claims WHERE milestone_id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (milestone_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "milestone_id": str(row[0]),
                    "streak_threshold": int(row[1]),
                    "claimed_at": str(row[2]),
                    "pack_id": str(row[3]),
                }
        return None

    def get_all_milestone_claims(self) -> List[dict]:
        """Fetch all claimed milestones."""
        sql = "SELECT milestone_id, streak_threshold, claimed_at, pack_id FROM milestone_claims ORDER BY streak_threshold ASC"
        with self.db.get_connection() as conn:
            cursor = conn.execute(sql)
            rows = cursor.fetchall()
            return [
                {
                    "milestone_id": str(r[0]),
                    "streak_threshold": int(r[1]),
                    "claimed_at": str(r[2]),
                    "pack_id": str(r[3]),
                }
                for r in rows
            ]

    def record_milestone_claim(
        self, milestone_id: str, streak_threshold: int, pack_id: str, claimed_at: str
    ) -> None:
        """Record that a milestone pack has been unlocked and claimed."""
        sql = "INSERT INTO milestone_claims (milestone_id, streak_threshold, claimed_at, pack_id) VALUES (?, ?, ?, ?)"
        with self.db.get_connection() as conn:
            conn.execute(sql, (milestone_id, streak_threshold, claimed_at, pack_id))

    def claim_daily_reward_atomic(
        self,
        claim_date: str,
        sticker_id: str,
        claimed_at: str,
        ownership: Optional[StickerOwnershipModel] = None,
    ) -> bool:
        """Atomically record daily claim and optional sticker ownership in a single transaction.

        Returns True if the claim was recorded, False if already claimed for claim_date.
        Guarantees that under concurrent or duplicate attempts, at most one caller succeeds,
        and no orphan ownership record is created.
        """
        claim_sql = "INSERT INTO daily_reward_claims (claim_date, sticker_id, claimed_at) VALUES (?, ?, ?)"
        ownership_sql = """
            INSERT INTO sticker_ownership (
                id, sticker_id, unlocked_at, unlock_reason, source
            ) VALUES (?, ?, ?, ?, ?)
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM daily_reward_claims WHERE claim_date = ?", (claim_date,)
                )
                if cursor.fetchone():
                    return False

                conn.execute(claim_sql, (claim_date, sticker_id, claimed_at))
                if ownership:
                    conn.execute(
                        ownership_sql,
                        (
                            ownership.id,
                            ownership.sticker_id,
                            ownership.unlocked_at,
                            ownership.unlock_reason,
                            ownership.source,
                        ),
                    )
                return True
        except sqlite3.IntegrityError:
            # UNIQUE constraint on daily_reward_claims.claim_date or sticker_ownership.sticker_id
            return False

    def claim_milestone_atomic(
        self,
        milestone_id: str,
        streak_threshold: int,
        pack_id: str,
        claimed_at: str,
        ownerships: List[StickerOwnershipModel],
    ) -> bool:
        """Atomically record milestone claim and included sticker ownerships in a single transaction.

        Returns True if newly claimed, False if milestone_id was already claimed.
        """
        claim_sql = "INSERT INTO milestone_claims (milestone_id, streak_threshold, claimed_at, pack_id) VALUES (?, ?, ?, ?)"
        ownership_sql = """
            INSERT OR IGNORE INTO sticker_ownership (
                id, sticker_id, unlocked_at, unlock_reason, source
            ) VALUES (?, ?, ?, ?, ?)
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM milestone_claims WHERE milestone_id = ?", (milestone_id,)
                )
                if cursor.fetchone():
                    return False

                conn.execute(claim_sql, (milestone_id, streak_threshold, claimed_at, pack_id))
                for o in ownerships:
                    conn.execute(
                        ownership_sql,
                        (o.id, o.sticker_id, o.unlocked_at, o.unlock_reason, o.source),
                    )
                return True
        except sqlite3.IntegrityError:
            return False


default_sticker_repository = StickerRepository()


def get_sticker_repository() -> StickerRepository:
    """FastAPI dependency provider for StickerRepository."""
    return default_sticker_repository
