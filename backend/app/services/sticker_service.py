"""TRACE Sticker Garden Service.

Coordinates sticker catalogue retrieval, user ownership lifecycle,
authoritative exploration streak tracking, and idempotent reward evaluation.
"""
from datetime import date, datetime, timedelta, timezone
import logging
from typing import List, Optional, Tuple
import uuid

from fastapi import Depends

from app.models.sticker import StickerDefinition, StickerOwnershipModel, StickerPackDefinition
from app.repositories.sticker_repository import StickerRepository, get_sticker_repository
from app.repositories.trace_repository import TraceRepository, get_trace_repository
from app.schemas.sticker import (
    MilestoneProgress,
    OwnedStickerResponse,
    StickerPackResponse,
    StickerResponse,
    StreakEvaluationResult,
    StreakSummaryResponse,
)
from app.stickers.catalogue import (
    REWARD_PACKS,
    get_all_packs,
    get_all_stickers,
    get_pack_by_id,
    get_sticker_by_id,
)

logger = logging.getLogger("trace.services.stickers")


class StickerError(Exception):
    """Base exception for Sticker Garden operations."""
    pass


class StickerNotFoundError(StickerError):
    """Raised when a referenced sticker or pack is not found in the catalogue."""
    pass


class StickerAlreadyOwnedError(StickerError):
    """Raised when an attempt is made to grant a sticker that the user already owns."""
    pass


class StickerService:
    """Coordinates Sticker Garden catalogue access, streak tracking, and rewards."""

    def __init__(
        self,
        repository: Optional[StickerRepository] = None,
        trace_repository: Optional[TraceRepository] = None,
    ):
        self._repository = repository
        self._trace_repository = trace_repository

    @property
    def repository(self) -> StickerRepository:
        return self._repository or get_sticker_repository()

    @property
    def trace_repository(self) -> TraceRepository:
        return self._trace_repository or get_trace_repository()

    @staticmethod
    def _to_sticker_response(definition: StickerDefinition) -> StickerResponse:
        return StickerResponse(
            id=definition.id,
            name=definition.name,
            description=definition.description,
            theme=definition.theme,  # type: ignore[arg-type]
            rarity=definition.rarity,  # type: ignore[arg-type]
            asset_path=definition.asset_path,
            unlock_type=definition.unlock_type,  # type: ignore[arg-type]
            tags=definition.tags,
            milestone_requirement=definition.milestone_requirement,
            is_asset_available=definition.is_asset_available,
        )

    @staticmethod
    def _to_pack_response(definition: StickerPackDefinition) -> StickerPackResponse:
        return StickerPackResponse(
            id=definition.id,
            name=definition.name,
            description=definition.description,
            milestone_requirement=definition.milestone_requirement,
            sticker_ids=definition.sticker_ids,
        )

    def _resolve_timezone(
        self,
        tz_offset_minutes: Optional[int] = None,
        tz_name: Optional[str] = None,
    ) -> timezone:
        """Resolve client's local timezone.
        
        Prioritizes tz_offset_minutes (standard JavaScript getTimezoneOffset()),
        then tz_name / offset string, with fallback to local system timezone or UTC.
        """
        if tz_offset_minutes is not None:
            try:
                # In JS, getTimezoneOffset() returns UTC - local (e.g. UTC+5:30 -> -330)
                return timezone(timedelta(minutes=-tz_offset_minutes))
            except Exception as exc:
                logger.debug("Failed resolving timezone from offset %s: %s", tz_offset_minutes, exc)

        if tz_name:
            if tz_name.upper() == "UTC":
                return timezone.utc
            if len(tz_name) in (5, 6) and (tz_name.startswith("+") or tz_name.startswith("-")):
                try:
                    sign = 1 if tz_name[0] == "+" else -1
                    parts = tz_name[1:].split(":")
                    hours = int(parts[0])
                    mins = int(parts[1]) if len(parts) > 1 else 0
                    return timezone(timedelta(minutes=sign * (hours * 60 + mins)))
                except Exception as exc:
                    logger.debug("Failed parsing offset string %s: %s", tz_name, exc)
            try:
                import zoneinfo
                return zoneinfo.ZoneInfo(tz_name)  # type: ignore[return-value]
            except Exception as exc:
                logger.debug("zoneinfo could not load %s: %s", tz_name, exc)

        # Fallback to local system timezone
        try:
            local_tz = datetime.now().astimezone().tzinfo
            if local_tz is not None:
                return local_tz  # type: ignore[return-value]
        except Exception:
            pass

        return timezone.utc

    def get_catalogue(self, theme: Optional[str] = None) -> List[StickerResponse]:
        """Retrieve all stickers defined in the catalogue, optionally filtered by theme."""
        stickers = get_all_stickers()
        if theme:
            stickers = [s for s in stickers if s.theme.lower() == theme.lower()]
        return [self._to_sticker_response(s) for s in stickers]

    def get_sticker(self, sticker_id: str) -> StickerResponse:
        """Retrieve a specific sticker definition by ID."""
        definition = get_sticker_by_id(sticker_id)
        if not definition:
            raise StickerNotFoundError(f"Sticker '{sticker_id}' not found in catalogue.")
        return self._to_sticker_response(definition)

    def get_packs(self) -> List[StickerPackResponse]:
        """Retrieve all defined reward packs."""
        packs = get_all_packs()
        return [self._to_pack_response(p) for p in packs]

    def get_pack(self, pack_id: str) -> StickerPackResponse:
        """Retrieve a specific pack definition by ID."""
        definition = get_pack_by_id(pack_id)
        if not definition:
            raise StickerNotFoundError(f"Sticker pack '{pack_id}' not found in catalogue.")
        return self._to_pack_response(definition)

    def get_user_collection(self) -> List[OwnedStickerResponse]:
        """Retrieve all stickers currently earned and owned by the user."""
        records = self.repository.get_all()
        collection: List[OwnedStickerResponse] = []
        for rec in records:
            definition = get_sticker_by_id(rec.sticker_id)
            if definition:
                collection.append(
                    OwnedStickerResponse(
                        id=rec.id,
                        sticker_id=rec.sticker_id,
                        unlocked_at=rec.unlocked_at,
                        unlock_reason=rec.unlock_reason,
                        source=rec.source,
                        sticker=self._to_sticker_response(definition),
                    )
                )
        return collection

    def grant_sticker(
        self,
        sticker_id: str,
        unlock_reason: str = "Granted to explorer collection",
        source: str = "manual_grant",
    ) -> OwnedStickerResponse:
        """Grant ownership of a sticker to the user.
        
        Validates the sticker against the catalogue and ensures a user
        cannot own the same sticker more than once.
        """
        definition = get_sticker_by_id(sticker_id)
        if not definition:
            raise StickerNotFoundError(f"Sticker '{sticker_id}' not found in catalogue.")

        existing = self.repository.get_by_sticker_id(sticker_id)
        if existing:
            raise StickerAlreadyOwnedError(f"Sticker '{sticker_id}' is already owned.")

        ownership_id = f"stick-own-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        ownership = StickerOwnershipModel(
            id=ownership_id,
            sticker_id=sticker_id,
            unlocked_at=now,
            unlock_reason=unlock_reason,
            source=source,
        )
        self.repository.create(ownership)
        logger.info("Granted sticker '%s' (%s) via %s", sticker_id, definition.name, source)

        return OwnedStickerResponse(
            id=ownership.id,
            sticker_id=ownership.sticker_id,
            unlocked_at=ownership.unlocked_at,
            unlock_reason=ownership.unlock_reason,
            source=ownership.source,
            sticker=self._to_sticker_response(definition),
        )

    def calculate_streak(
        self,
        tz_offset_minutes: Optional[int] = None,
        tz_name: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> Tuple[int, int, int, bool, date]:
        """Derive exploration streak strictly from persisted traces in SQLite.
        
        Rules:
        - A qualifying day is a local calendar day with >=1 saved trace.
        - Multiple traces on the same calendar day count as ONE day.
        - Consecutive qualifying days form the active streak.
        - If today has no trace yet, but yesterday had a trace, the streak is alive
          and pending today's trace.
        - If yesterday also had no trace, the current streak is 0.
        - Longest streak tracks the maximum consecutive qualifying day run in history.
        
        Returns:
            (current_streak, longest_streak, total_qualifying_days, today_qualified, today_date)
        """
        target_tz = self._resolve_timezone(tz_offset_minutes, tz_name)
        if now is not None:
            now_dt = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
            now_local = now_dt.astimezone(target_tz)
        else:
            now_local = datetime.now(target_tz)
        today_date = now_local.date()

        timestamps = self.trace_repository.get_all_created_timestamps()
        qualifying_dates_set = set()

        for ts_str in timestamps:
            try:
                # Normalize ISO timestamp
                normalized = ts_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(normalized)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                local_dt = dt.astimezone(target_tz)
                qualifying_dates_set.add(local_dt.date())
            except Exception as exc:
                logger.warning("Failed parsing trace created_at '%s': %s", ts_str, exc)

        qualifying_dates = sorted(qualifying_dates_set)
        total_qualifying_days = len(qualifying_dates)
        today_qualified = today_date in qualifying_dates_set

        # Calculate current consecutive streak
        current_streak = 0
        if today_qualified:
            current_streak = 1
            check_date = today_date - timedelta(days=1)
            while check_date in qualifying_dates_set:
                current_streak += 1
                check_date -= timedelta(days=1)
        else:
            yesterday = today_date - timedelta(days=1)
            if yesterday in qualifying_dates_set:
                current_streak = 1
                check_date = yesterday - timedelta(days=1)
                while check_date in qualifying_dates_set:
                    current_streak += 1
                    check_date -= timedelta(days=1)
            else:
                current_streak = 0

        # Calculate longest contiguous streak across history
        longest_streak = 0
        if qualifying_dates:
            max_run = 1
            curr_run = 1
            for i in range(1, len(qualifying_dates)):
                if qualifying_dates[i] == qualifying_dates[i - 1] + timedelta(days=1):
                    curr_run += 1
                else:
                    curr_run = 1
                if curr_run > max_run:
                    max_run = curr_run
            longest_streak = max(max_run, current_streak)

        return current_streak, longest_streak, total_qualifying_days, today_qualified, today_date

    def calculate_streak_summary(
        self,
        tz_offset_minutes: Optional[int] = None,
        tz_name: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> StreakSummaryResponse:
        """Pure read-only computation of exploration streak and milestone progression.

        Performs zero mutations (no inserts, updates, deletes, or claims). Reads exclusively from
        persisted traces, daily reward claims, sticker ownership, and milestone claims.
        """
        current_streak, longest_streak, total_qualifying_days, today_qualified, today_date = (
            self.calculate_streak(tz_offset_minutes, tz_name, now=now)
        )
        today_iso = today_date.isoformat()

        # Check existing daily claim
        existing_daily_claim = self.repository.get_daily_claim(today_iso)

        if existing_daily_claim:
            today_reward_claimed = True
            today_reward_available = False
            today_reward_reason = "Daily exploration sticker already claimed for today."
        else:
            today_reward_claimed = False
            owned_records = self.repository.get_all()
            owned_sticker_ids = {r.sticker_id for r in owned_records}
            all_starters = [s for s in get_all_stickers() if s.unlock_type == "starter"]
            available_starters = [s for s in all_starters if s.id not in owned_sticker_ids]

            if not available_starters:
                today_reward_available = False
                today_reward_reason = (
                    "All catalogue daily stickers collected! Check back as new editions arrive."
                )
            else:
                today_reward_available = True
                if today_qualified:
                    today_reward_reason = "Today's exploration trace recorded."
                else:
                    today_reward_reason = "Record an exploration trace today to earn your daily sticker."

        # Read claimed milestones
        claimed_milestone_dict = {
            m["milestone_id"]: m for m in self.repository.get_all_milestone_claims()
        }

        # Order packs by threshold: 7, 30, 50, 100
        sorted_packs = sorted(
            REWARD_PACKS,
            key=lambda p: int(p.milestone_requirement.get("threshold", 0)),
        )

        milestone_status_list: List[MilestoneProgress] = []
        next_milestone_found = False
        next_milestone_days: Optional[int] = None
        days_to_next_milestone: Optional[int] = None

        for pack in sorted_packs:
            threshold = int(pack.milestone_requirement.get("threshold", 0))
            milestone_id = f"milestone-{threshold}d"
            claim = claimed_milestone_dict.get(milestone_id)
            is_achieved = claim is not None
            days_remaining = max(0, threshold - current_streak)

            is_current = False
            if not is_achieved and not next_milestone_found:
                is_current = True
                next_milestone_found = True
                next_milestone_days = threshold
                days_to_next_milestone = days_remaining

            milestone_status_list.append(
                MilestoneProgress(
                    id=milestone_id,
                    name=pack.name,
                    streak_threshold=threshold,
                    pack_id=pack.id,
                    is_achieved=is_achieved,
                    is_current=is_current,
                    is_locked=not is_achieved,
                    days_remaining=days_remaining,
                    claimed_at=claim["claimed_at"] if claim else None,
                )
            )

        total_stickers_owned = self.repository.count()

        return StreakSummaryResponse(
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_qualifying_days=total_qualifying_days,
            today_qualified=today_qualified,
            today_reward_claimed=today_reward_claimed,
            today_reward_available=today_reward_available,
            today_reward_reason=today_reward_reason,
            next_milestone_days=next_milestone_days,
            days_to_next_milestone=days_to_next_milestone,
            total_stickers_owned=total_stickers_owned,
            milestones=milestone_status_list,
        )

    def evaluate_rewards(
        self,
        tz_offset_minutes: Optional[int] = None,
        tz_name: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> StreakEvaluationResult:
        """Evaluate daily sticker rewards and milestone pack unlocks idempotently.
        
        Ensures:
        - Max 1 daily sticker per qualifying day.
        - Overlapping ownership never crashes (UNIQUE constraint protected).
        - Milestone packs unlock only once per threshold achievement.
        - If no starter stickers remain, cleanly reports unavailability without crashing.
        """
        current_streak, longest_streak, total_qualifying_days, today_qualified, today_date = (
            self.calculate_streak(tz_offset_minutes, tz_name, now=now)
        )
        today_iso = today_date.isoformat()
        eval_now_dt = now if now is not None else datetime.now(timezone.utc)
        if eval_now_dt.tzinfo is None:
            eval_now_dt = eval_now_dt.replace(tzinfo=timezone.utc)
        now_iso = eval_now_dt.astimezone(timezone.utc).isoformat()

        daily_sticker_awarded: Optional[OwnedStickerResponse] = None
        streak_extended = False

        # 1. Daily reward evaluation (strictly at most 1 daily sticker per local calendar day)
        existing_daily_claim = self.repository.get_daily_claim(today_iso)

        if not existing_daily_claim and today_qualified:
            # User qualified today and hasn't claimed yet.
            owned_records = self.repository.get_all()
            owned_sticker_ids = {r.sticker_id for r in owned_records}
            all_starters = [s for s in get_all_stickers() if s.unlock_type == "starter"]
            available_starters = [s for s in all_starters if s.id not in owned_sticker_ids]

            if available_starters:
                chosen = available_starters[0]
                ownership_id = f"stick-own-{uuid.uuid4().hex[:12]}"
                ownership = StickerOwnershipModel(
                    id=ownership_id,
                    sticker_id=chosen.id,
                    unlocked_at=now_iso,
                    unlock_reason=f"Daily reward for exploration on {today_iso}",
                    source="daily_reward",
                )
                claimed = self.repository.claim_daily_reward_atomic(
                    claim_date=today_iso,
                    sticker_id=chosen.id,
                    claimed_at=now_iso,
                    ownership=ownership,
                )
                if claimed:
                    daily_sticker_awarded = OwnedStickerResponse(
                        id=ownership_id,
                        sticker_id=chosen.id,
                        unlocked_at=now_iso,
                        unlock_reason=ownership.unlock_reason,
                        source="daily_reward",
                        sticker=self._to_sticker_response(chosen),
                    )
                    streak_extended = True
                    logger.info("Awarded daily sticker %s on %s", chosen.id, today_iso)
                else:
                    logger.info("Daily claim for %s already claimed by concurrent evaluation", today_iso)
            else:
                # All starter stickers owned; mark claim atomically so we don't re-evaluate today
                claimed = self.repository.claim_daily_reward_atomic(
                    claim_date=today_iso,
                    sticker_id="none_available",
                    claimed_at=now_iso,
                    ownership=None,
                )
                if claimed:
                    streak_extended = True

        # 2. Milestone pack unlocking
        milestones_unlocked: List[StickerPackResponse] = []
        claimed_milestone_dict = {
            m["milestone_id"]: m for m in self.repository.get_all_milestone_claims()
        }

        # Order packs by threshold: 7, 30, 50, 100
        sorted_packs = sorted(
            REWARD_PACKS,
            key=lambda p: int(p.milestone_requirement.get("threshold", 0)),
        )

        for pack in sorted_packs:
            threshold = int(pack.milestone_requirement.get("threshold", 0))
            milestone_id = f"milestone-{threshold}d"

            if milestone_id not in claimed_milestone_dict:
                if current_streak >= threshold:
                    now_iso = datetime.now(timezone.utc).isoformat()
                    owned_ids = {r.sticker_id for r in self.repository.get_all()}

                    pack_ownerships: List[StickerOwnershipModel] = []
                    for s_id in pack.sticker_ids:
                        if s_id not in owned_ids:
                            pack_ownerships.append(
                                StickerOwnershipModel(
                                    id=f"stick-own-{uuid.uuid4().hex[:12]}",
                                    sticker_id=s_id,
                                    unlocked_at=now_iso,
                                    unlock_reason=f"Earned with {pack.name} ({threshold}-day milestone)",
                                    source="milestone_reward",
                                )
                            )

                    claimed = self.repository.claim_milestone_atomic(
                        milestone_id=milestone_id,
                        streak_threshold=threshold,
                        pack_id=pack.id,
                        claimed_at=now_iso,
                        ownerships=pack_ownerships,
                    )
                    if claimed:
                        claimed_milestone_dict[milestone_id] = {
                            "milestone_id": milestone_id,
                            "streak_threshold": threshold,
                            "pack_id": pack.id,
                            "claimed_at": now_iso,
                        }
                        milestones_unlocked.append(self._to_pack_response(pack))
                        logger.info("Unlocked milestone pack %s at %d days", pack.id, threshold)

        streak_summary = self.calculate_streak_summary(
            tz_offset_minutes=tz_offset_minutes, tz_name=tz_name, now=now
        )
        if daily_sticker_awarded:
            streak_summary = streak_summary.model_copy(
                update={"today_reward_reason": f"Earned '{daily_sticker_awarded.sticker.name}' for exploring today!"}
            )

        return StreakEvaluationResult(
            daily_sticker_awarded=daily_sticker_awarded,
            milestones_unlocked=milestones_unlocked,
            streak_summary=streak_summary,
            streak_extended=streak_extended,
        )

    def get_streak_summary(
        self,
        tz_offset_minutes: Optional[int] = None,
        tz_name: Optional[str] = None,
    ) -> StreakSummaryResponse:
        """Retrieve authoritative streak summary without modifying reward or ownership state."""
        return self.calculate_streak_summary(tz_offset_minutes=tz_offset_minutes, tz_name=tz_name)


default_sticker_service = StickerService()


def get_sticker_service(
    repository: StickerRepository = Depends(get_sticker_repository),
    trace_repository: TraceRepository = Depends(get_trace_repository),
) -> StickerService:
    """FastAPI dependency provider for StickerService."""
    return StickerService(repository=repository, trace_repository=trace_repository)
