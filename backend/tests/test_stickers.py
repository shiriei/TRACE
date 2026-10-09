"""Tests for Sticker Garden Collection Foundation.

Verifies:
- Catalogue uniqueness and stability (12-16 starter stickers).
- Pack definitions reference valid catalogue sticker IDs.
- Catalogue and pack metadata validation across all 6 themes.
- SQLite persistence of sticker ownership records.
- Duplicate ownership prevention (user cannot own the same sticker more than once).
- Safe failure when granting unknown sticker IDs.
- Accurate unlock metadata persistence (timestamp, reason, source).
- Independence from traces and attachments (zero regressions).
"""
from datetime import datetime, timedelta, timezone
import pytest
import sqlite3
from fastapi.testclient import TestClient

from app.db.database import SQLiteDatabase
from app.main import app
from app.models.sticker import StickerOwnershipModel
from app.models.trace import TraceModel
from app.repositories.sticker_repository import StickerRepository, get_sticker_repository
from app.repositories.trace_repository import TraceRepository, get_trace_repository
from app.repositories.attachment_repository import AttachmentRepository, get_attachment_repository
from app.services.media_storage import MediaStorageService, get_media_storage
from app.stickers.catalogue import (
    REWARD_PACKS,
    STARTER_STICKERS,
    get_all_packs,
    get_all_stickers,
    get_pack_by_id,
    get_sticker_by_id,
)


@pytest.fixture
def sticker_db_env(tmp_path):
    """Provides isolated SQLite database and overrides dependencies."""
    db_file = tmp_path / "sticker_test.db"
    media_dir = tmp_path / "test_media"
    media_dir.mkdir(exist_ok=True)

    db_instance = SQLiteDatabase(db_path=str(db_file))
    sticker_repo = StickerRepository(database=db_instance)
    trace_repo = TraceRepository(database=db_instance)
    attach_repo = AttachmentRepository(database=db_instance)
    storage_svc = MediaStorageService(media_dir=str(media_dir))

    app.dependency_overrides[get_sticker_repository] = lambda: sticker_repo
    app.dependency_overrides[get_trace_repository] = lambda: trace_repo
    app.dependency_overrides[get_attachment_repository] = lambda: attach_repo
    app.dependency_overrides[get_media_storage] = lambda: storage_svc

    yield sticker_repo

    app.dependency_overrides.pop(get_sticker_repository, None)
    app.dependency_overrides.pop(get_trace_repository, None)
    app.dependency_overrides.pop(get_attachment_repository, None)
    app.dependency_overrides.pop(get_media_storage, None)


@pytest.fixture(autouse=True)
def mock_default_ai():
    """Default AI mock so tests execute instantly without network calls."""
    from unittest.mock import AsyncMock, patch
    from app.ai.schemas import TraceAIResult

    default_result = TraceAIResult(
        category="Personal",
        title="Field Observation",
        summary="A notable observation in the physical surroundings.",
        tags=["field", "observation"],
        sensory_type="visual",
        confidence=0.85,
    )
    with patch(
        "app.services.trace_service.ai_service.interpret_observation",
        new_callable=AsyncMock,
        return_value=default_result,
    ) as mock:
        yield mock


@pytest.fixture
def client(sticker_db_env):
    """TestClient bound to the isolated database environment."""
    return TestClient(app)


# =====================================================================
# 1. Catalogue & Pack Metadata Tests
# =====================================================================

def test_catalogue_entries_have_unique_stable_ids():
    """1. Every catalogue entry has a unique, stable identifier."""
    stickers = get_all_stickers()
    assert 12 <= len(stickers) <= 16, f"Expected 12-16 starter stickers, got {len(stickers)}"

    ids = [s.id for s in stickers]
    assert len(ids) == len(set(ids)), "All sticker IDs must be strictly unique"

    for sticker in stickers:
        assert sticker.id.startswith("sticker-"), f"Sticker ID '{sticker.id}' must follow 'sticker-' convention"
        assert len(sticker.id) > 10, "Sticker ID must be descriptive"


def test_all_pack_sticker_references_point_to_valid_catalogue_ids():
    """2. All pack definitions reference existing, valid sticker catalogue IDs."""
    packs = get_all_packs()
    assert len(packs) == 4, "Must define the 4 required reward packs"

    pack_ids = {p.id for p in packs}
    expected_pack_ids = {
        "pack-little-things-7d",
        "pack-field-journal-30d",
        "pack-outside-ish-50d",
        "pack-world-noticed-100d",
    }
    assert pack_ids == expected_pack_ids, f"Expected pack IDs {expected_pack_ids}, got {pack_ids}"

    catalogue_ids = {s.id for s in get_all_stickers()}

    for pack in packs:
        assert len(pack.sticker_ids) > 0, f"Pack '{pack.id}' has no stickers assigned"
        for s_id in pack.sticker_ids:
            assert s_id in catalogue_ids, f"Pack '{pack.id}' references unknown sticker '{s_id}'"


def test_catalogue_and_pack_metadata_validation():
    """3. Catalogue entries cover all 6 required themes with complete metadata."""
    stickers = get_all_stickers()
    required_themes = {"botanical", "creatures", "vintage", "humor", "cozy", "planner"}
    observed_themes = {s.theme for s in stickers}

    assert required_themes.issubset(observed_themes), f"Missing themes: {required_themes - observed_themes}"

    valid_rarities = {"common", "uncommon", "rare", "legendary"}
    for s in stickers:
        assert s.name.strip(), f"Sticker {s.id} has empty name"
        assert s.description.strip(), f"Sticker {s.id} has empty description/caption"
        assert s.rarity in valid_rarities, f"Sticker {s.id} has invalid rarity: {s.rarity}"
        assert s.asset_path.startswith("assets/stickers/"), f"Sticker {s.id} asset path invalid: {s.asset_path}"
        assert s.asset_path.endswith(".png"), f"Sticker {s.id} asset must be transparent PNG: {s.asset_path}"
        assert isinstance(s.tags, list) and len(s.tags) >= 2, f"Sticker {s.id} must have searchable tags"
        assert isinstance(s.is_asset_available, bool)


# =====================================================================
# 2. Catalogue API Endpoints
# =====================================================================

def test_api_list_stickers_and_theme_filter(client):
    """API endpoint returns the full catalogue and supports theme filtering."""
    # List all
    res = client.get("/api/v1/stickers")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == len(STARTER_STICKERS)

    # Filter by theme
    res_botanical = client.get("/api/v1/stickers?theme=botanical")
    assert res_botanical.status_code == 200
    botanical_data = res_botanical.json()
    assert len(botanical_data) > 0
    assert all(s["theme"] == "botanical" for s in botanical_data)

    # Filter by creatures
    res_creatures = client.get("/api/v1/stickers?theme=creatures")
    assert res_creatures.status_code == 200
    creatures_data = res_creatures.json()
    assert all(s["theme"] == "creatures" for s in creatures_data)


def test_api_get_single_sticker(client):
    """API endpoint returns a single sticker definition or 404 if missing."""
    res = client.get("/api/v1/stickers/sticker-sprout-alive")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "sticker-sprout-alive"
    assert data["name"] == "Tiny Sprout"
    assert data["theme"] == "botanical"

    res_missing = client.get("/api/v1/stickers/sticker-nonexistent-mystery")
    assert res_missing.status_code == 404


def test_api_list_packs(client):
    """API endpoint returns all reward packs."""
    res = client.get("/api/v1/stickers/packs")
    assert res.status_code == 200
    packs = res.json()
    assert len(packs) == 4
    pack_names = [p["name"] for p in packs]
    assert "The Little Things Club" in pack_names
    assert "The Field Journal Collection" in pack_names
    assert "The Outside-ish Personality Pack" in pack_names
    assert "The World Noticed Collection" in pack_names


# =====================================================================
# 3. Ownership Persistence & Duplicate Prevention
# =====================================================================

def test_ownership_saved_and_retrieved_from_sqlite(client, sticker_db_env):
    """Ownership record is persisted to SQLite and retrievable via API."""
    # Initial collection is empty
    empty_res = client.get("/api/v1/stickers/collection")
    assert empty_res.status_code == 200
    assert empty_res.json() == []

    # Grant a sticker
    grant_res = client.post(
        "/api/v1/stickers/collection/grant",
        json={
            "sticker_id": "sticker-sprout-alive",
            "unlock_reason": "First outdoor walk completed",
            "source": "milestone_reward",
        },
    )
    assert grant_res.status_code == 201
    grant_data = grant_res.json()
    assert grant_data["sticker_id"] == "sticker-sprout-alive"
    assert grant_data["unlock_reason"] == "First outdoor walk completed"
    assert grant_data["source"] == "milestone_reward"
    assert grant_data["sticker"]["name"] == "Tiny Sprout"

    # Collection now contains the granted sticker
    coll_res = client.get("/api/v1/stickers/collection")
    assert coll_res.status_code == 200
    collection = coll_res.json()
    assert len(collection) == 1
    assert collection[0]["sticker_id"] == "sticker-sprout-alive"
    assert collection[0]["sticker"]["theme"] == "botanical"

    # Directly verify in SQLite repository
    record = sticker_db_env.get_by_sticker_id("sticker-sprout-alive")
    assert record is not None
    assert record.unlock_reason == "First outdoor walk completed"
    assert record.source == "milestone_reward"


def test_duplicate_ownership_is_prevented(client, sticker_db_env):
    """User cannot own the same sticker more than once."""
    payload = {
        "sticker_id": "sticker-snail-schedule",
        "unlock_reason": "Walked at dusk",
        "source": "daily_reward",
    }

    # First grant succeeds
    res1 = client.post("/api/v1/stickers/collection/grant", json=payload)
    assert res1.status_code == 201

    # Second grant fails with 409 Conflict
    res2 = client.post("/api/v1/stickers/collection/grant", json=payload)
    assert res2.status_code == 409
    assert "already owned" in res2.json()["detail"].lower()

    # Database only contains 1 record
    assert sticker_db_env.count() == 1

    # Direct database insertion also fails UNIQUE constraint
    with pytest.raises(sqlite3.IntegrityError):
        duplicate_model = StickerOwnershipModel(
            id="stick-own-dup-test",
            sticker_id="sticker-snail-schedule",
            unlocked_at="2026-10-10T00:00:00Z",
            unlock_reason="Duplicate test",
            source="manual_grant",
        )
        sticker_db_env.create(duplicate_model)


def test_granting_unknown_sticker_id_fails_safely(client, sticker_db_env):
    """Attempting to grant an unknown sticker ID fails safely with 404."""
    res = client.post(
        "/api/v1/stickers/collection/grant",
        json={
            "sticker_id": "sticker-nonexistent-mystery-creature",
            "unlock_reason": "Attempting bad grant",
            "source": "manual_grant",
        },
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
    assert sticker_db_env.count() == 0


def test_unlock_metadata_persisted_correctly(client, sticker_db_env):
    """Metadata (reason, source, timestamp) is accurately preserved and formatted."""
    res = client.post(
        "/api/v1/stickers/collection/grant",
        json={
            "sticker_id": "sticker-touched-grass",
            "unlock_reason": "Touched real grass after 4 hours of coding",
            "source": "manual_grant",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["unlock_reason"] == "Touched real grass after 4 hours of coding"
    assert data["source"] == "manual_grant"
    assert "T" in data["unlocked_at"]  # Valid ISO format


# =====================================================================
# 4. Isolation from Existing Traces & Attachments
# =====================================================================

def test_sticker_operations_do_not_affect_traces(client):
    """Trace creation, retrieval, and deletion remain completely unaffected."""
    # 1. Create a physical trace
    trace_res = client.post(
        "/api/v1/traces",
        json={
            "observation": "Wild thyme flowering in stone steps.",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "location_mode": "manual",
        },
    )
    assert trace_res.status_code == 201
    trace_id = trace_res.json()["id"]

    # 2. Grant a sticker
    sticker_res = client.post(
        "/api/v1/stickers/collection/grant",
        json={"sticker_id": "sticker-rock-lichen"},
    )
    assert sticker_res.status_code == 201

    # 3. Verify trace is unaffected
    fetch_trace = client.get(f"/api/v1/traces/{trace_id}")
    assert fetch_trace.status_code == 200
    assert fetch_trace.json()["id"] == trace_id

    # 4. Verify deleting trace does not affect user stickers
    del_trace = client.delete(f"/api/v1/traces/{trace_id}")
    assert del_trace.status_code == 200

    collection_res = client.get("/api/v1/stickers/collection")
    assert collection_res.status_code == 200
    assert len(collection_res.json()) == 2
    owned_ids = {s["sticker_id"] for s in collection_res.json()}
    assert "sticker-rock-lichen" in owned_ids


# =====================================================================
# 5. Exploration Streak Calculation & Reward Idempotency Tests
# =====================================================================

def test_streak_summary_empty_database(client):
    """Zero traces in database yields 0 streak and correct initial state."""
    res = client.get("/api/v1/stickers/streak")
    assert res.status_code == 200
    data = res.json()
    assert data["current_streak"] == 0
    assert data["longest_streak"] == 0
    assert data["total_qualifying_days"] == 0
    assert data["today_qualified"] is False
    assert data["today_reward_claimed"] is False
    assert data["today_reward_available"] is True
    assert data["total_stickers_owned"] == 0
    assert len(data["milestones"]) == 4
    assert data["milestones"][0]["is_current"] is True
    assert data["milestones"][0]["is_achieved"] is False
    assert data["days_to_next_milestone"] == 7


def test_streak_single_trace_today_awards_daily_sticker(client):
    """Creating 1 trace today yields streak=1, today_qualified=True, and awards 1 daily sticker."""
    create_res = client.post(
        "/api/v1/traces",
        json={"observation": "Morning dew on oak leaf."},
    )
    assert create_res.status_code == 201

    res = client.get("/api/v1/stickers/streak")
    assert res.status_code == 200
    data = res.json()
    assert data["current_streak"] == 1
    assert data["longest_streak"] == 1
    assert data["total_qualifying_days"] == 1
    assert data["today_qualified"] is True
    assert data["today_reward_claimed"] is True
    assert data["total_stickers_owned"] == 1

    # Check collection has this daily sticker
    collection_res = client.get("/api/v1/stickers/collection")
    assert collection_res.status_code == 200
    assert len(collection_res.json()) == 1
    assert collection_res.json()[0]["source"] == "daily_reward"


def test_multiple_traces_on_same_day_count_as_one_and_do_not_duplicate(client):
    """Multiple traces on the same calendar day count as ONE day and award at most 1 sticker."""
    # Create 3 traces on the same day
    for obs in ["Spotted a blue jay.", "Found a smooth river pebble.", "Fern unfurling in shade."]:
        r = client.post("/api/v1/traces", json={"observation": obs})
        assert r.status_code == 201

    res = client.get("/api/v1/stickers/streak")
    assert res.status_code == 200
    data = res.json()
    assert data["current_streak"] == 1
    assert data["total_qualifying_days"] == 1
    assert data["total_stickers_owned"] == 1

    # Refreshing or requesting evaluate again never duplicates rewards
    eval_res = client.post("/api/v1/stickers/streak/evaluate")
    assert eval_res.status_code == 200
    assert eval_res.json()["daily_sticker_awarded"] is None
    assert eval_res.json()["streak_summary"]["total_stickers_owned"] == 1


def test_consecutive_days_streak_and_milestone_unlock(client, sticker_db_env):
    """7 consecutive qualifying days unlocks 7-day milestone pack and awards pack stickers."""
    trace_repo = TraceRepository(database=sticker_db_env.db)
    now_utc = datetime.now(timezone.utc)

    # Insert traces across 7 consecutive calendar days (6 days ago through today)
    for day_offset in range(6, -1, -1):
        trace_time = (now_utc - timedelta(days=day_offset)).isoformat()
        trace_model = TraceModel(
            id=f"hist-trace-{day_offset}",
            observation=f"Exploration entry from {day_offset} days ago",
            category="Nature",
            title=f"Walk Day {day_offset}",
            summary="Walk summary",
            tags=[],
            sensory_type="visual",
            confidence=0.9,
            latitude=51.5,
            longitude=-0.1,
            location_mode="manual",
            created_at=trace_time,
        )
        trace_repo.create(trace_model)

    # Verify that GET is read-only: streak is 7, but milestone is not achieved prior to evaluation
    pre_res = client.get("/api/v1/stickers/streak")
    assert pre_res.status_code == 200
    pre_data = pre_res.json()
    assert pre_data["current_streak"] == 7
    m7_pre = [m for m in pre_data["milestones"] if m["streak_threshold"] == 7][0]
    assert m7_pre["is_achieved"] is False
    assert m7_pre["days_remaining"] == 0

    # Evaluate rewards explicitly
    eval_res = client.post("/api/v1/stickers/streak/evaluate")
    assert eval_res.status_code == 200
    assert len(eval_res.json()["milestones_unlocked"]) >= 1

    # Read-only GET now reflects persisted achieved state
    res = client.get("/api/v1/stickers/streak")
    assert res.status_code == 200
    data = res.json()
    assert data["current_streak"] == 7
    assert data["longest_streak"] == 7
    assert data["total_qualifying_days"] == 7
    assert data["today_qualified"] is True

    # 7-day milestone is achieved
    m7 = [m for m in data["milestones"] if m["streak_threshold"] == 7][0]
    assert m7["is_achieved"] is True
    assert m7["days_remaining"] == 0

    # 30-day milestone is the next immediate target
    m30 = [m for m in data["milestones"] if m["streak_threshold"] == 30][0]
    assert m30["is_current"] is True
    assert m30["is_achieved"] is False
    assert m30["days_remaining"] == 23
    assert data["days_to_next_milestone"] == 23


def test_missing_day_resets_current_streak_but_preserves_longest_and_stickers(client, sticker_db_env):
    """A broken streak sets current_streak=0 while keeping longest_streak and previously earned stickers."""
    trace_repo = TraceRepository(database=sticker_db_env.db)
    now_utc = datetime.now(timezone.utc)

    # 4 consecutive days of traces ending 3 days ago (gap of 2 days: yesterday and 2 days ago missed)
    for day_offset in range(6, 2, -1):
        trace_time = (now_utc - timedelta(days=day_offset)).isoformat()
        trace_model = TraceModel(
            id=f"gap-trace-{day_offset}",
            observation=f"Historic trace {day_offset} days ago",
            category="Nature",
            title="Old Walk",
            summary="Old Walk summary",
            tags=[],
            sensory_type="visual",
            confidence=0.8,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at=trace_time,
        )
        trace_repo.create(trace_model)

    # First evaluate to grant any historic stickers
    res = client.get("/api/v1/stickers/streak")
    assert res.status_code == 200
    data = res.json()
    assert data["current_streak"] == 0  # Broken streak because neither today nor yesterday had a trace
    assert data["longest_streak"] == 4
    assert data["total_qualifying_days"] == 4
    assert data["today_qualified"] is False


def test_milestone_claim_idempotency_prevents_duplicate_awards(client, sticker_db_env):
    """Reaching or re-evaluating an achieved milestone never grants duplicate claims or throws errors."""
    trace_repo = TraceRepository(database=sticker_db_env.db)
    now_utc = datetime.now(timezone.utc)

    for day_offset in range(6, -1, -1):
        trace_time = (now_utc - timedelta(days=day_offset)).isoformat()
        trace_repo.create(
            TraceModel(
                id=f"idem-trace-{day_offset}",
                observation=f"Idempotent test trace {day_offset}",
                category="General",
                title="Trace",
                summary="Summary",
                tags=[],
                sensory_type="visual",
                confidence=0.5,
                latitude=None,
                longitude=None,
                location_mode="unplaced",
                created_at=trace_time,
            )
        )

    # Evaluate multiple times
    res1 = client.post("/api/v1/stickers/streak/evaluate")
    assert res1.status_code == 200
    assert len(res1.json()["milestones_unlocked"]) >= 1

    res2 = client.post("/api/v1/stickers/streak/evaluate")
    assert res2.status_code == 200
    assert len(res2.json()["milestones_unlocked"]) == 0  # Already claimed! No duplicates


def test_trace_creation_resilience_when_reward_evaluation_errors(client, monkeypatch):
    """Trace creation succeeds safely even if sticker reward engine encounters an unexpected exception."""
    from app.services.sticker_service import StickerService

    def broken_eval(*args, **kwargs):
        raise RuntimeError("Simulated transient reward engine failure")

    monkeypatch.setattr(StickerService, "evaluate_rewards", broken_eval)

    create_res = client.post(
        "/api/v1/traces",
        json={"observation": "Resilience observation test."},
    )
    # Must succeed regardless of reward engine error!
    assert create_res.status_code == 201
    assert "id" in create_res.json()


def test_create_trace_returns_daily_reward_on_first_trace_and_none_on_second(client):
    """Trace creation returns daily_sticker_awarded on the first trace of a day and None on the second."""
    # 1. First trace of today
    res1 = client.post(
        "/api/v1/traces",
        json={"observation": "Morning dew on fresh moss in garden wall.", "tz_offset_minutes": 0},
    )
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["reward"] is not None
    assert data1["reward"]["daily_sticker_awarded"] is not None
    awarded = data1["reward"]["daily_sticker_awarded"]
    assert "sticker" in awarded
    assert awarded["source"] == "daily_reward"
    assert data1["reward"]["streak_summary"]["current_streak"] == 1
    assert data1["reward"]["streak_summary"]["today_qualified"] is True

    # 2. Second trace of today
    res2 = client.post(
        "/api/v1/traces",
        json={"observation": "Afternoon dragonfly hovering near stream.", "tz_offset_minutes": 0},
    )
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["reward"] is not None
    # No new daily sticker for second trace on the same day!
    assert data2["reward"]["daily_sticker_awarded"] is None
    assert data2["reward"]["streak_summary"]["current_streak"] == 1

    # 3. Collection verification: exactly 1 sticker earned
    coll_res = client.get("/api/v1/stickers/collection")
    assert coll_res.status_code == 200
    assert len(coll_res.json()) == 1


def test_reward_celebration_milestone_unlocked_without_daily_sticker(client, sticker_db_env):
    """When starter sticker pool is exhausted but Day 7 milestone is reached, milestone unlocks without daily sticker."""
    now_utc = datetime.now(timezone.utc)
    trace_repo = TraceRepository(database=sticker_db_env.db)

    # Pre-grant all starter stickers so starter pool is exhausted
    all_starters = [s for s in get_all_stickers() if s.unlock_type == "starter"]
    for s in all_starters:
        sticker_db_env.create(
            StickerOwnershipModel(
                id=f"own-{s.id}",
                sticker_id=s.id,
                unlocked_at=now_utc.isoformat(),
                unlock_reason="Pre-collected",
                source="manual_grant",
            )
        )

    # Seed 6 consecutive prior days (days -6 through -1)
    for day_offset in range(6, 0, -1):
        ts = (now_utc - timedelta(days=day_offset)).isoformat()
        trace_repo.create(
            TraceModel(
                id=f"streak-day-{day_offset}",
                observation=f"Observing prior day {day_offset}",
                category="Nature",
                title=f"Day -{day_offset}",
                summary="",
                tags=[],
                sensory_type="visual",
                confidence=0.9,
                latitude=None,
                longitude=None,
                location_mode="unplaced",
                created_at=ts,
            )
        )

    # Save qualifying trace today -> Day 7 milestone achieved!
    res = client.post(
        "/api/v1/traces",
        json={"observation": "Day 7 milestone observation on trail.", "tz_offset_minutes": 0},
    )
    assert res.status_code == 201
    data = res.json()
    reward = data["reward"]
    assert reward is not None
    assert reward["streak_extended"] is True
    assert reward["streak_summary"]["current_streak"] == 7
    # Starter pool exhausted -> no daily sticker
    assert reward["daily_sticker_awarded"] is None
    # But milestone pack was unlocked!
    assert len(reward["milestones_unlocked"]) == 1
    pack = reward["milestones_unlocked"][0]
    assert pack["id"] == "pack-little-things-7d"
    assert pack["name"] == "The Little Things Club"


def test_reward_celebration_streak_extended_when_pool_exhausted_without_milestone(client, sticker_db_env):
    """When starter pool is exhausted and no milestone is reached, streak_extended is True on first trace and False on second."""
    now_utc = datetime.now(timezone.utc)
    trace_repo = TraceRepository(database=sticker_db_env.db)

    # Pre-grant all starter stickers
    for s in get_all_stickers():
        if s.unlock_type == "starter":
            sticker_db_env.create(
                StickerOwnershipModel(
                    id=f"own-{s.id}",
                    sticker_id=s.id,
                    unlocked_at=now_utc.isoformat(),
                    unlock_reason="Pre-collected",
                    source="manual_grant",
                )
            )

    # Seed 2 consecutive prior days
    for day_offset in (2, 1):
        ts = (now_utc - timedelta(days=day_offset)).isoformat()
        trace_repo.create(
            TraceModel(
                id=f"streak-prior-{day_offset}",
                observation=f"Prior day {day_offset}",
                category="Nature",
                title=f"Prior {day_offset}",
                summary="",
                tags=[],
                sensory_type="visual",
                confidence=0.9,
                latitude=None,
                longitude=None,
                location_mode="unplaced",
                created_at=ts,
            )
        )

    # 1. First trace of today: streak extends to Day 3
    res1 = client.post(
        "/api/v1/traces",
        json={"observation": "Day 3 observation with full starter pool.", "tz_offset_minutes": 0},
    )
    assert res1.status_code == 201
    r1 = res1.json()["reward"]
    assert r1["streak_extended"] is True
    assert r1["daily_sticker_awarded"] is None
    assert len(r1["milestones_unlocked"]) == 0
    assert r1["streak_summary"]["current_streak"] == 3

    # 2. Second trace on same day: neither daily sticker nor milestone nor streak extension
    res2 = client.post(
        "/api/v1/traces",
        json={"observation": "Second trace on Day 3.", "tz_offset_minutes": 0},
    )
    assert res2.status_code == 201
    r2 = res2.json()["reward"]
    assert r2["streak_extended"] is False
    assert r2["daily_sticker_awarded"] is None
    assert len(r2["milestones_unlocked"]) == 0
    assert r2["streak_summary"]["current_streak"] == 3


def test_reward_celebration_daily_sticker_plus_milestone(client, sticker_db_env):
    """When day 7 milestone is reached and starter stickers are available, both daily sticker and milestone pack are awarded."""
    now_utc = datetime.now(timezone.utc)
    trace_repo = TraceRepository(database=sticker_db_env.db)

    # Seed 6 consecutive prior days (user has NOT exhausted starter stickers)
    for day_offset in range(6, 0, -1):
        ts = (now_utc - timedelta(days=day_offset)).isoformat()
        trace_repo.create(
            TraceModel(
                id=f"combo-day-{day_offset}",
                observation=f"Observing prior day {day_offset}",
                category="Nature",
                title=f"Combo {day_offset}",
                summary="",
                tags=[],
                sensory_type="visual",
                confidence=0.9,
                latitude=None,
                longitude=None,
                location_mode="unplaced",
                created_at=ts,
            )
        )

    res = client.post(
        "/api/v1/traces",
        json={"observation": "Day 7 milestone observation with starter sticker available.", "tz_offset_minutes": 0},
    )
    assert res.status_code == 201
    reward = res.json()["reward"]
    assert reward["streak_extended"] is True
    assert reward["streak_summary"]["current_streak"] == 7
    # Both daily sticker AND milestone pack are present!
    assert reward["daily_sticker_awarded"] is not None
    assert reward["daily_sticker_awarded"]["source"] == "daily_reward"
    assert len(reward["milestones_unlocked"]) == 1
    assert reward["milestones_unlocked"][0]["id"] == "pack-little-things-7d"


# =====================================================================
# 5. Read-Only Streak Endpoint Verification Tests
# =====================================================================

def test_streak_get_leaves_all_reward_tables_unchanged(client, sticker_db_env):
    """Calling GET /api/v1/stickers/streak leaves all reward-related SQLite tables completely unchanged."""
    trace_repo = TraceRepository(database=sticker_db_env.db)
    now_utc = datetime.now(timezone.utc)

    # Seed traces directly into repository (bypassing evaluation)
    trace_repo.create(
        TraceModel(
            id="read-only-trace-1",
            observation="Seed observation directly into DB",
            category="Nature",
            title="Seed Trace",
            summary="Seed summary",
            tags=[],
            sensory_type="visual",
            confidence=0.9,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at=now_utc.isoformat(),
        )
    )

    def get_table_counts():
        with sticker_db_env.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sticker_ownership")
            c_ownership = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM daily_reward_claims")
            c_daily = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM milestone_claims")
            c_milestone = cursor.fetchone()[0]
            return c_ownership, c_daily, c_milestone

    initial_counts = get_table_counts()
    assert initial_counts == (0, 0, 0)

    # Call GET /api/v1/stickers/streak multiple times with various parameters
    for _ in range(5):
        res = client.get("/api/v1/stickers/streak")
        assert res.status_code == 200

    res_tz = client.get("/api/v1/stickers/streak?tz_offset_minutes=-300")
    assert res_tz.status_code == 200

    after_counts = get_table_counts()
    assert after_counts == initial_counts == (0, 0, 0), "GET /streak must not mutate SQLite tables"


def test_direct_database_trace_without_reward_evaluation_does_not_claim_rewards(client, sticker_db_env):
    """A direct database trace without reward evaluation does not cause GET to claim a sticker."""
    trace_repo = TraceRepository(database=sticker_db_env.db)
    now_utc = datetime.now(timezone.utc)

    trace_repo.create(
        TraceModel(
            id="direct-trace-unclaimed",
            observation="Directly inserted trace without POST /traces",
            category="Urban",
            title="Direct Trace",
            summary="",
            tags=[],
            sensory_type="visual",
            confidence=0.8,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at=now_utc.isoformat(),
        )
    )

    # GET returns streak info with today_qualified=True, but today_reward_claimed=False
    res = client.get("/api/v1/stickers/streak")
    assert res.status_code == 200
    data = res.json()
    assert data["today_qualified"] is True
    assert data["today_reward_claimed"] is False
    assert data["total_stickers_owned"] == 0

    # User collection remains completely empty
    coll_res = client.get("/api/v1/stickers/collection")
    assert coll_res.status_code == 200
    assert len(coll_res.json()) == 0


def test_trace_saved_through_normal_creation_flow_evaluates_and_persists_reward(client):
    """A trace saved through the normal creation flow still evaluates and persists the correct reward."""
    res = client.post(
        "/api/v1/traces",
        json={"observation": "Watching morning birds near riverbank.", "tz_offset_minutes": 0},
    )
    assert res.status_code == 201
    reward = res.json()["reward"]
    assert reward is not None
    assert reward["daily_sticker_awarded"] is not None
    assert reward["streak_extended"] is True

    # Reading the summary via GET with matching timezone returns the persisted state
    streak_res = client.get("/api/v1/stickers/streak?tz_offset_minutes=0")
    assert streak_res.status_code == 200
    streak_data = streak_res.json()
    assert streak_data["today_qualified"] is True
    assert streak_data["today_reward_claimed"] is True
    assert streak_data["total_stickers_owned"] == 1

    # User collection confirms persistence
    coll_res = client.get("/api/v1/stickers/collection")
    assert coll_res.status_code == 200
    assert len(coll_res.json()) == 1
    assert coll_res.json()[0]["sticker_id"] == reward["daily_sticker_awarded"]["sticker_id"]


def test_timezone_aware_streak_calculations_read_only(client, sticker_db_env):
    """Timezone-aware streak calculations evaluate accurately across local calendar days without side effects."""
    trace_repo = TraceRepository(database=sticker_db_env.db)

    # Fixed UTC timestamp: 2026-05-10T23:30:00Z
    # In UTC (+00:00): date is 2026-05-10
    # In JST (+09:00, tz_offset_minutes=-540): local time is 2026-05-11 08:30:00, date is 2026-05-11
    # In EDT (-04:00, tz_offset_minutes=240): local time is 2026-05-10 19:30:00, date is 2026-05-10
    trace_repo.create(
        TraceModel(
            id="tz-test-trace",
            observation="Timezone boundary observation",
            category="Nature",
            title="TZ Trace",
            summary="",
            tags=[],
            sensory_type="visual",
            confidence=0.9,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at="2026-05-10T23:30:00Z",
        )
    )

    # Query with offset 0 (UTC)
    res_utc = client.get("/api/v1/stickers/streak?tz_offset_minutes=0")
    assert res_utc.status_code == 200
    data_utc = res_utc.json()
    assert data_utc["total_qualifying_days"] == 1

    # Query with offset -540 (JST)
    res_jst = client.get("/api/v1/stickers/streak?tz_offset_minutes=-540")
    assert res_jst.status_code == 200
    data_jst = res_jst.json()
    assert data_jst["total_qualifying_days"] == 1

    # Ensure no claims or sticker records were created
    coll_res = client.get("/api/v1/stickers/collection")
    assert coll_res.status_code == 200
    assert len(coll_res.json()) == 0


# =====================================================================
# 10. Regression Tests — One Daily Sticker Enforcement & Concurrency
# =====================================================================

def test_two_traces_on_same_day_awards_at_most_one_daily_sticker(client, sticker_db_env):
    """Subsequent qualifying traces on the same local day must NOT award another daily sticker."""
    today_iso = datetime.now(timezone.utc).date().isoformat()

    # Trace 1 on today's local day
    res1 = client.post(
        "/api/v1/traces",
        json={
            "observation": "First morning trace: spotted yellow dandelions by the old curb.",
            "tz_offset_minutes": 0,
        },
    )
    assert res1.status_code == 201
    trace1_data = res1.json()
    assert trace1_data["reward"] is not None
    assert trace1_data["reward"]["daily_sticker_awarded"] is not None
    assert trace1_data["reward"]["streak_extended"] is True

    # Assert exactly 1 ownership record and 1 daily claim persisted
    assert sticker_db_env.count() == 1
    assert sticker_db_env.get_daily_claim(today_iso) is not None

    # Trace 2 on the SAME day
    res2 = client.post(
        "/api/v1/traces",
        json={
            "observation": "Second afternoon trace: spotted bumblebee hovering over clover.",
            "tz_offset_minutes": 0,
        },
    )
    assert res2.status_code == 201
    trace2_data = res2.json()
    assert trace2_data["reward"] is not None
    # Must NOT award another daily sticker!
    assert trace2_data["reward"]["daily_sticker_awarded"] is None
    assert trace2_data["reward"]["streak_extended"] is False

    # Persisted ownership and claim counts must remain strictly 1
    assert sticker_db_env.count() == 1
    with sticker_db_env.db.get_connection() as conn:
        claim_count = conn.execute("SELECT COUNT(*) FROM daily_reward_claims").fetchone()[0]
        assert claim_count == 1


def test_concurrent_reward_evaluation(client, sticker_db_env):
    """Concurrent reward evaluation requests for the same day award exactly 1 sticker atomically."""
    import concurrent.futures
    from app.services.sticker_service import StickerService

    trace_repo = TraceRepository(database=sticker_db_env.db)
    today_iso = datetime.now(timezone.utc).date().isoformat()

    # Seed a trace for today
    trace_repo.create(
        TraceModel(
            id="concurrent-trace-1",
            observation="A quiet cedar tree on a cloudy morning.",
            category="Nature",
            title="Cedar Tree",
            summary="",
            tags=[],
            sensory_type="visual",
            confidence=0.9,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at=f"{today_iso}T09:00:00Z",
        )
    )

    # Function executed concurrently across threads
    def run_eval():
        # Create service instance bound to the isolated test db
        svc = StickerService(repository=sticker_db_env, trace_repository=trace_repo)
        return svc.evaluate_rewards(tz_offset_minutes=0)

    # Launch 10 concurrent evaluations
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_eval) for _ in range(10)]
        results = [f.result() for f in futures]

    awarded_results = [r for r in results if r.daily_sticker_awarded is not None]
    extended_results = [r for r in results if r.streak_extended is True]

    # Exactly 1 thread must succeed in awarding the daily sticker and extending streak
    assert len(awarded_results) == 1, f"Expected 1 award, got {len(awarded_results)}"
    assert len(extended_results) == 1, f"Expected 1 streak_extended, got {len(extended_results)}"

    # Database must have exactly 1 sticker ownership and 1 daily claim
    assert sticker_db_env.count() == 1
    with sticker_db_env.db.get_connection() as conn:
        claim_count = conn.execute("SELECT COUNT(*) FROM daily_reward_claims").fetchone()[0]
        assert claim_count == 1


def test_new_local_day_awards_second_sticker(client, sticker_db_env):
    """The first trace on day 1 awards sticker 1; the first trace on day 2 awards sticker 2."""
    trace_repo = TraceRepository(database=sticker_db_env.db)
    from app.services.sticker_service import StickerService
    svc = StickerService(repository=sticker_db_env, trace_repository=trace_repo)

    # Day 1: 2026-08-01
    trace_repo.create(
        TraceModel(
            id="day1-trace",
            observation="Day 1 morning observation.",
            category="Nature",
            title="Day 1",
            summary="",
            tags=[],
            sensory_type="visual",
            confidence=0.9,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at="2026-08-01T10:00:00Z",
        )
    )

    day1_now = datetime(2026, 8, 1, 10, 5, tzinfo=timezone.utc)
    res_day1 = svc.evaluate_rewards(tz_offset_minutes=0, now=day1_now)
    assert res_day1.daily_sticker_awarded is not None
    assert res_day1.streak_extended is True
    assert sticker_db_env.count() == 1

    # Day 2: 2026-08-02
    trace_repo.create(
        TraceModel(
            id="day2-trace",
            observation="Day 2 morning observation.",
            category="Nature",
            title="Day 2",
            summary="",
            tags=[],
            sensory_type="visual",
            confidence=0.9,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at="2026-08-02T10:00:00Z",
        )
    )

    day2_now = datetime(2026, 8, 2, 10, 5, tzinfo=timezone.utc)
    res_day2 = svc.evaluate_rewards(tz_offset_minutes=0, now=day2_now)
    assert res_day2.daily_sticker_awarded is not None
    assert res_day2.streak_extended is True
    assert res_day2.streak_summary.current_streak == 2
    assert sticker_db_env.count() == 2

    # Second trace on Day 2 must NOT award a third sticker
    trace_repo.create(
        TraceModel(
            id="day2-trace-afternoon",
            observation="Day 2 afternoon observation.",
            category="Nature",
            title="Day 2 afternoon",
            summary="",
            tags=[],
            sensory_type="visual",
            confidence=0.9,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at="2026-08-02T16:00:00Z",
        )
    )
    day2_afternoon = datetime(2026, 8, 2, 16, 5, tzinfo=timezone.utc)
    res_day2_repeat = svc.evaluate_rewards(tz_offset_minutes=0, now=day2_afternoon)
    assert res_day2_repeat.daily_sticker_awarded is None
    assert res_day2_repeat.streak_extended is False
    assert sticker_db_env.count() == 2


def test_timezone_boundaries_daily_reward(client, sticker_db_env):
    """Enforces calendar-day determination under client timezone offsets."""
    trace_repo = TraceRepository(database=sticker_db_env.db)
    from app.services.sticker_service import StickerService
    svc = StickerService(repository=sticker_db_env, trace_repository=trace_repo)

    # Trace saved at 2026-09-10 23:00:00 UTC
    # In UTC+5:30 (India, offset -330): local time is 2026-09-11 04:30:00 (Date is Sept 11)
    trace_repo.create(
        TraceModel(
            id="tz-bound-trace",
            observation="Midnight observation near boundary.",
            category="Nature",
            title="Boundary Trace",
            summary="",
            tags=[],
            sensory_type="visual",
            confidence=0.9,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at="2026-09-10T23:00:00Z",
        )
    )

    eval_now = datetime(2026, 9, 10, 23, 10, tzinfo=timezone.utc)
    # Evaluate in UTC+5:30 (tz_offset_minutes = -330)
    res_ist = svc.evaluate_rewards(tz_offset_minutes=-330, now=eval_now)
    # Target date should be 2026-09-11
    assert sticker_db_env.get_daily_claim("2026-09-11") is not None
    assert sticker_db_env.count() == 1
    assert res_ist.daily_sticker_awarded is not None

    # Subsequent evaluation on the same local date (tz_offset_minutes = -330)
    eval_repeat = datetime(2026, 9, 10, 23, 20, tzinfo=timezone.utc)
    res_ist_repeat = svc.evaluate_rewards(tz_offset_minutes=-330, now=eval_repeat)
    assert res_ist_repeat.daily_sticker_awarded is None
    assert sticker_db_env.count() == 1


def test_milestone_plus_daily_rewards_on_milestone_day(client, sticker_db_env):
    """Milestone pack unlocks independently alongside daily reward on eligible milestone day."""
    trace_repo = TraceRepository(database=sticker_db_env.db)
    from app.services.sticker_service import StickerService
    svc = StickerService(repository=sticker_db_env, trace_repository=trace_repo)

    # Seed 6 previous consecutive days of traces: 2026-01-01 through 2026-01-06
    for day in range(1, 7):
        trace_repo.create(
            TraceModel(
                id=f"streak-seed-{day}",
                observation=f"Day {day} observation.",
                category="Nature",
                title=f"Day {day}",
                summary="",
                tags=[],
                sensory_type="visual",
                confidence=0.9,
                latitude=None,
                longitude=None,
                location_mode="unplaced",
                created_at=f"2026-01-0{day}T12:00:00Z",
            )
        )
        # Mark daily claims for days 1..6
        sticker_db_env.record_daily_claim(
            claim_date=f"2026-01-0{day}",
            sticker_id=f"seed-sticker-{day}",
            claimed_at=f"2026-01-0{day}T12:00:00Z",
        )

    # Day 7 trace: 2026-01-07 reaches the 7-day milestone!
    trace_repo.create(
        TraceModel(
            id="streak-seed-7",
            observation="Day 7 observation reaching milestone.",
            category="Nature",
            title="Day 7",
            summary="",
            tags=[],
            sensory_type="visual",
            confidence=0.9,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at="2026-01-07T12:00:00Z",
        )
    )

    day7_now = datetime(2026, 1, 7, 12, 5, tzinfo=timezone.utc)
    res_day7 = svc.evaluate_rewards(tz_offset_minutes=0, now=day7_now)

    # Daily sticker awarded
    assert res_day7.daily_sticker_awarded is not None
    assert res_day7.streak_extended is True
    assert res_day7.streak_summary.current_streak == 7

    # Milestone pack unlocked
    assert len(res_day7.milestones_unlocked) == 1
    assert res_day7.milestones_unlocked[0].id == "pack-little-things-7d"

    # Milestone claim record persisted
    claim_7d = sticker_db_env.get_milestone_claim("milestone-7d")
    assert claim_7d is not None
    assert claim_7d["pack_id"] == "pack-little-things-7d"

    # Second trace on Day 7:
    trace_repo.create(
        TraceModel(
            id="streak-seed-7-evening",
            observation="Day 7 evening trace.",
            category="Nature",
            title="Day 7 evening",
            summary="",
            tags=[],
            sensory_type="visual",
            confidence=0.9,
            latitude=None,
            longitude=None,
            location_mode="unplaced",
            created_at="2026-01-07T18:00:00Z",
        )
    )
    day7_evening = datetime(2026, 1, 7, 18, 5, tzinfo=timezone.utc)
    res_day7_second = svc.evaluate_rewards(tz_offset_minutes=0, now=day7_evening)
    # Neither daily sticker nor milestone pack should unlock again
    assert res_day7_second.daily_sticker_awarded is None
    assert len(res_day7_second.milestones_unlocked) == 0
    assert res_day7_second.streak_extended is False


