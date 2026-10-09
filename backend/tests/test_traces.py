"""Tests for TRACE Persistence and Trace API Endpoints."""
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.ai.exceptions import AIServiceUnavailableError, AITimeoutError
from app.ai.schemas import TraceAIResult
from app.db.database import SQLiteDatabase
from app.main import app
from app.models.trace import TraceModel
from app.repositories.trace_repository import TraceRepository, get_trace_repository


from app.repositories.attachment_repository import AttachmentRepository, get_attachment_repository
from app.services.media_storage import MediaStorageService, get_media_storage


@pytest.fixture
def test_db_repo(tmp_path):
    """Fixture providing an isolated SQLite database and repository for each test."""
    db_file = tmp_path / "traces_test.db"
    media_dir = tmp_path / "traces_media"
    media_dir.mkdir(exist_ok=True)

    db_instance = SQLiteDatabase(db_path=str(db_file))
    repo_instance = TraceRepository(database=db_instance)
    attach_repo = AttachmentRepository(database=db_instance)
    storage_svc = MediaStorageService(media_dir=str(media_dir))

    # Override dependencies in FastAPI app
    app.dependency_overrides[get_trace_repository] = lambda: repo_instance
    app.dependency_overrides[get_attachment_repository] = lambda: attach_repo
    app.dependency_overrides[get_media_storage] = lambda: storage_svc

    yield repo_instance

    app.dependency_overrides.pop(get_trace_repository, None)
    app.dependency_overrides.pop(get_attachment_repository, None)
    app.dependency_overrides.pop(get_media_storage, None)



@pytest.fixture(autouse=True)
def mock_default_ai():
    """Default AI mock so tests execute instantly without real network calls."""
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
def client(test_db_repo):
    """Test client bound to isolated repository."""
    return TestClient(app)


# =====================================================================
# 1. Location Placement Modes Tests (Phase 3 Step 2)
# =====================================================================

def test_create_trace_with_gps_location(client):
    """1. Create trace with GPS location and location_mode='gps'."""
    payload = {
        "observation": "Wild clover patch buzzing with bumblebees.",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "location_mode": "gps",
    }
    response = client.post("/api/v1/traces", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["latitude"] == 51.5074
    assert data["longitude"] == -0.1278
    assert data["location_mode"] == "gps"


def test_create_trace_with_manual_location(client):
    """2. Create trace with manual location and location_mode='manual'."""
    payload = {
        "observation": "Old water fountain turned into a miniature planter.",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "location_mode": "manual",
    }
    response = client.post("/api/v1/traces", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["latitude"] == 48.8566
    assert data["longitude"] == 2.3522
    assert data["location_mode"] == "manual"


def test_create_trace_without_location(client):
    """3. Create trace without location (location_mode='unplaced', coordinates=None)."""
    payload = {
        "observation": "A mysterious distant chime carried on the wind.",
        "location_mode": "unplaced",
    }
    response = client.post("/api/v1/traces", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["location_mode"] == "unplaced"


def test_retrieve_gps_trace(client):
    """4. Retrieve a GPS-placed trace."""
    created = client.post(
        "/api/v1/traces",
        json={
            "observation": "Rusted surveyor anchor bolt.",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location_mode": "gps",
        },
    ).json()

    res = client.get(f"/api/v1/traces/{created['id']}")
    assert res.status_code == 200
    fetched = res.json()
    assert fetched["id"] == created["id"]
    assert fetched["location_mode"] == "gps"
    assert fetched["latitude"] == 37.7749
    assert fetched["longitude"] == -122.4194


def test_retrieve_manually_placed_trace(client):
    """5. Retrieve a manually placed trace."""
    created = client.post(
        "/api/v1/traces",
        json={
            "observation": "Hand-painted sign on alley gate.",
            "latitude": 34.0522,
            "longitude": -118.2437,
            "location_mode": "manual",
        },
    ).json()

    res = client.get(f"/api/v1/traces/{created['id']}")
    assert res.status_code == 200
    fetched = res.json()
    assert fetched["id"] == created["id"]
    assert fetched["location_mode"] == "manual"
    assert fetched["latitude"] == 34.0522
    assert fetched["longitude"] == -118.2437


def test_retrieve_unplaced_trace(client):
    """6. Retrieve an unplaced trace."""
    created = client.post(
        "/api/v1/traces",
        json={
            "observation": "Fleeting scent of cedar smoke.",
            "location_mode": "unplaced",
        },
    ).json()

    res = client.get(f"/api/v1/traces/{created['id']}")
    assert res.status_code == 200
    fetched = res.json()
    assert fetched["id"] == created["id"]
    assert fetched["location_mode"] == "unplaced"
    assert fetched["latitude"] is None
    assert fetched["longitude"] is None


def test_delete_trace_endpoint(client):
    """7. Delete trace removes it from the system."""
    created = client.post(
        "/api/v1/traces",
        json={
            "observation": "Discarded wooden spool.",
            "location_mode": "unplaced",
        },
    ).json()

    del_res = client.delete(f"/api/v1/traces/{created['id']}")
    assert del_res.status_code == 200
    assert del_res.json()["id"] == created["id"]

    assert client.get(f"/api/v1/traces/{created['id']}").status_code == 404


def test_location_mode_returned_correctly_by_api(client):
    """10. Location mode is returned correctly in listing and single-item responses."""
    t_gps = client.post(
        "/api/v1/traces",
        json={"observation": "GPS trace", "latitude": 10.0, "longitude": 20.0, "location_mode": "gps"},
    ).json()
    t_man = client.post(
        "/api/v1/traces",
        json={"observation": "Manual trace", "latitude": 30.0, "longitude": 40.0, "location_mode": "manual"},
    ).json()
    t_unp = client.post(
        "/api/v1/traces",
        json={"observation": "Unplaced trace", "location_mode": "unplaced"},
    ).json()

    list_res = client.get("/api/v1/traces")
    assert list_res.status_code == 200
    traces = {t["id"]: t for t in list_res.json()}

    assert traces[t_gps["id"]]["location_mode"] == "gps"
    assert traces[t_man["id"]]["location_mode"] == "manual"
    assert traces[t_unp["id"]]["location_mode"] == "unplaced"
    assert traces[t_unp["id"]]["latitude"] is None


# =====================================================================
# 2. Inconsistent & Invalid Location Validation Tests
# =====================================================================

@pytest.mark.parametrize(
    "payload",
    [
        # Unplaced with coordinates is invalid
        {"observation": "Test", "latitude": 10.0, "longitude": 20.0, "location_mode": "unplaced"},
        # GPS without coordinates is invalid
        {"observation": "Test", "location_mode": "gps"},
        {"observation": "Test", "latitude": 10.0, "location_mode": "gps"},
        # Manual without coordinates is invalid
        {"observation": "Test", "location_mode": "manual"},
        {"observation": "Test", "longitude": 20.0, "location_mode": "manual"},
        # Latitude out of bounds
        {"observation": "Test", "latitude": 95.0, "longitude": 20.0, "location_mode": "manual"},
        # Longitude out of bounds
        {"observation": "Test", "latitude": 10.0, "longitude": 185.0, "location_mode": "manual"},
        # Empty observation
        {"observation": "", "latitude": 10.0, "longitude": 20.0},
        {"observation": "   \n\t  "},
        # Only one coordinate provided without explicit mode
        {"observation": "Test", "latitude": 10.0},
        {"observation": "Test", "longitude": 20.0},
    ],
)
def test_invalid_location_and_input_combinations(client, payload):
    """Inconsistent coordinate/mode states and invalid inputs return 422."""
    response = client.post("/api/v1/traces", json=payload)
    assert response.status_code == 422


# =====================================================================
# 3. Existing Trace Lifecycle Tests (Preserved)
# =====================================================================

def test_create_text_trace(client):
    """POST /api/v1/traces creates and persists a valid text trace."""
    payload = {
        "observation": "Wild mint growing beside a broken stone fountain.",
        "latitude": 37.7749,
        "longitude": -122.4194,
    }

    with patch("app.services.trace_service.ai_service.interpret_observation", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = TraceAIResult(
            category="Nature",
            title="Wild Mint by Stone Fountain",
            summary="Wild mint growing beside a broken stone fountain.",
            tags=["mint", "fountain"],
            sensory_type="environmental",
            confidence=0.91,
        )

        response = client.post("/api/v1/traces", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["id"].startswith("trace-")
        assert data["observation"] == "Wild mint growing beside a broken stone fountain."
        assert data["category"] == "Nature"
        assert data["title"] == "Wild Mint by Stone Fountain"
        assert data["summary"] == "Wild mint growing beside a broken stone fountain."
        assert "mint" in data["tags"]
        assert data["sensory_type"] == "environmental"
        assert data["confidence"] == 0.91
        assert data["latitude"] == 37.7749
        assert data["longitude"] == -122.4194
        assert data["location_mode"] == "manual"
        assert data["photo_path"] is None
        assert data["audio_path"] is None
        assert data["created_at"] is not None


def test_retrieve_one_trace(client):
    """GET /api/v1/traces/{trace_id} returns existing trace or 404."""
    create_res = client.post(
        "/api/v1/traces",
        json={
            "observation": "An ornate brass door handle shaped like a lion.",
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
    )
    assert create_res.status_code == 201
    trace_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/traces/{trace_id}")
    assert get_res.status_code == 200
    fetched = get_res.json()
    assert fetched["id"] == trace_id
    assert fetched["observation"] == "An ornate brass door handle shaped like a lion."
    assert fetched["latitude"] == 40.7128
    assert fetched["longitude"] == -74.0060

    missing_res = client.get("/api/v1/traces/non-existent-trace-id")
    assert missing_res.status_code == 404
    assert "not found" in missing_res.json()["detail"].lower()


def test_retrieve_trace_list(client):
    """GET /api/v1/traces returns a list of recorded traces."""
    obs_list = [
        ("Crumbling brick chimney covered in ivy", 34.05, -118.25),
        ("Rhythmic bell chiming from an unseen clock tower", 34.06, -118.24),
        ("Unmarked wooden gate leading into overgrown alley", 34.07, -118.26),
    ]

    created_ids = []
    for obs, lat, lng in obs_list:
        res = client.post(
            "/api/v1/traces",
            json={"observation": obs, "latitude": lat, "longitude": lng},
        )
        assert res.status_code == 201
        created_ids.append(res.json()["id"])

    list_res = client.get("/api/v1/traces")
    assert list_res.status_code == 200
    traces = list_res.json()
    assert isinstance(traces, list)
    assert len(traces) == 3

    retrieved_ids = [t["id"] for t in traces]
    for cid in created_ids:
        assert cid in retrieved_ids


def test_delete_trace(client):
    """DELETE /api/v1/traces/{trace_id} removes trace from storage."""
    create_res = client.post(
        "/api/v1/traces",
        json={
            "observation": "Faint chalk markings on the cobblestones.",
            "latitude": 48.8566,
            "longitude": 2.3522,
        },
    )
    trace_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/traces/{trace_id}")
    assert del_res.status_code == 200
    assert del_res.json()["id"] == trace_id

    get_res = client.get(f"/api/v1/traces/{trace_id}")
    assert get_res.status_code == 404

    del_again = client.delete(f"/api/v1/traces/{trace_id}")
    assert del_again.status_code == 404


def test_ai_success(client):
    """Trace creation populates AI-derived metadata when LM Studio succeeds."""
    ai_result = TraceAIResult(
        category="Structure",
        title="Sunken Stone Aqueduct",
        summary="Segment of an ancient brick aqueduct exposed by drainage works.",
        tags=["aqueduct", "masonry", "brick"],
        sensory_type="visual",
        confidence=0.97,
    )

    with patch("app.services.trace_service.ai_service.interpret_observation", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = ai_result

        response = client.post(
            "/api/v1/traces",
            json={
                "observation": "Found a sunken brick aqueduct section beneath the canal footpath.",
                "latitude": 51.5074,
                "longitude": -0.1278,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "Structure"
        assert data["title"] == "Sunken Stone Aqueduct"
        assert data["summary"] == "Segment of an ancient brick aqueduct exposed by drainage works."
        assert data["tags"] == ["aqueduct", "masonry", "brick"]
        assert data["sensory_type"] == "visual"
        assert data["confidence"] == 0.97

        stored_res = client.get(f"/api/v1/traces/{data['id']}")
        assert stored_res.status_code == 200
        assert stored_res.json()["title"] == "Sunken Stone Aqueduct"


def test_ai_unavailable_while_trace_creation_still_succeeds(client):
    """Trace is still successfully persisted if local AI is offline."""
    with patch("app.services.trace_service.ai_service.interpret_observation", new_callable=AsyncMock) as mock_ai:
        mock_ai.side_effect = AIServiceUnavailableError("LM Studio not running")

        response = client.post(
            "/api/v1/traces",
            json={
                "observation": "Low resonance vibration near the substation perimeter.",
                "latitude": 52.5200,
                "longitude": 13.4050,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["observation"] == "Low resonance vibration near the substation perimeter."
        assert data["confidence"] == 0.0
        assert data["category"] == "Personal"
        assert data["latitude"] == 52.5200
        assert data["longitude"] == 13.4050

        fetch_res = client.get(f"/api/v1/traces/{data['id']}")
        assert fetch_res.status_code == 200
        assert fetch_res.json()["id"] == data["id"]


def test_ai_timeout_while_trace_creation_still_succeeds(client):
    """Trace is saved even if local AI experiences timeout."""
    with patch("app.services.trace_service.ai_service.interpret_observation", new_callable=AsyncMock) as mock_ai:
        mock_ai.side_effect = AITimeoutError()

        response = client.post(
            "/api/v1/traces",
            json={
                "observation": "Small bird flock circling over the willow copse.",
                "latitude": 51.1789,
                "longitude": -1.8262,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["confidence"] == 0.0


def test_persistence_across_database_sessions(tmp_path):
    """Traces written in one DB session remain fully intact in a new session."""
    db_file = tmp_path / "cross_session_traces.db"

    # Session 1: Write Trace
    db_session1 = SQLiteDatabase(db_path=str(db_file))
    repo_session1 = TraceRepository(database=db_session1)

    trace = TraceModel(
        id="trace-session-test-01",
        observation="Hand-carved date '1894' etched into the cornerstone.",
        category="Structure",
        title="Cornerstone Inscription 1894",
        summary="Carved date of 1894 visible on the sandstone cornerstone.",
        tags=["inscription", "stone", "date", "1894"],
        sensory_type="visual",
        confidence=0.88,
        latitude=45.5017,
        longitude=-73.5673,
        location_mode="gps",
        created_at="2026-10-09T02:00:00+00:00",
        photo_path="storage/photos/cornerstone.jpg",
        audio_path="storage/audio/chime.wav",
    )
    repo_session1.create(trace)

    del repo_session1
    del db_session1

    # Session 2: Connect Anew
    db_session2 = SQLiteDatabase(db_path=str(db_file))
    repo_session2 = TraceRepository(database=db_session2)

    retrieved = repo_session2.get_by_id("trace-session-test-01")
    assert retrieved is not None
    assert retrieved.id == "trace-session-test-01"
    assert retrieved.location_mode == "gps"
    assert retrieved.latitude == 45.5017
    assert retrieved.longitude == -73.5673
    assert retrieved.photo_path == "storage/photos/cornerstone.jpg"
    assert retrieved.audio_path == "storage/audio/chime.wav"

    all_traces = repo_session2.get_all()
    assert len(all_traces) == 1
    assert all_traces[0].id == "trace-session-test-01"
    assert all_traces[0].location_mode == "gps"


# =====================================================================
# Regression Tests for UI Alignment & Duplicate Protection
# =====================================================================

def test_double_click_creates_only_one_trace(client, test_db_repo):
    """Simulating rapid double-clicks creates only one trace in the repository."""
    payload = {
        "observation": "A cluster of wild bluebells growing near the roots of an oak tree.",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "location_mode": "manual",
    }
    # Send first click
    resp1 = client.post("/api/v1/traces", json=payload)
    assert resp1.status_code == 201
    trace1 = resp1.json()

    # Send rapid second click (within dedup window)
    resp2 = client.post("/api/v1/traces", json=payload)
    assert resp2.status_code == 201
    trace2 = resp2.json()

    # Both requests return the same trace ID
    assert trace1["id"] == trace2["id"]

    # Repository contains only ONE trace
    all_traces = test_db_repo.get_all()
    matching = [t for t in all_traces if t.observation == payload["observation"]]
    assert len(matching) == 1


def test_duplicate_protection_does_not_block_separate_legitimate_traces(client, test_db_repo):
    """Traces with different coordinates or modes are not blocked."""
    payload1 = {
        "observation": "Interesting moss patch on stone.",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "location_mode": "manual",
    }
    payload2 = {
        "observation": "Interesting moss patch on stone.",
        "latitude": 51.5090,
        "longitude": -0.1290,
        "location_mode": "gps",
    }
    resp1 = client.post("/api/v1/traces", json=payload1)
    resp2 = client.post("/api/v1/traces", json=payload2)
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["id"] != resp2.json()["id"]

    all_traces = test_db_repo.get_all()
    assert len(all_traces) == 2


def test_failed_creation_retains_ability_to_retry(client, test_db_repo):
    """If a database/storage failure occurs, retrying creates the trace successfully."""
    from unittest.mock import patch
    payload = {
        "observation": "Unusual bird call echoing in the alley.",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "location_mode": "gps",
    }

    # Simulate transient DB failure on first call
    with pytest.raises(RuntimeError):
        with patch.object(test_db_repo, "create", side_effect=RuntimeError("Transient DB error")):
            client.post("/api/v1/traces", json=payload)

    # User retries the request
    resp2 = client.post("/api/v1/traces", json=payload)
    assert resp2.status_code == 201
    assert resp2.json()["observation"] == payload["observation"]

    all_traces = test_db_repo.get_all()
    assert len(all_traces) == 1


def test_delete_trace_removes_from_backend(client, test_db_repo):
    """Deleting a trace removes it from the backend and returns success."""
    # 1. Create a trace
    create_res = client.post(
        "/api/v1/traces",
        json={
            "observation": "Old water fountain embedded in the school wall.",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "location_mode": "manual",
        },
    )
    assert create_res.status_code == 201
    trace_id = create_res.json()["id"]

    # 2. Delete the trace
    del_res = client.delete(f"/api/v1/traces/{trace_id}")
    assert del_res.status_code == 200
    assert del_res.json()["id"] == trace_id

    # 3. Verify it is gone from database
    get_res = client.get(f"/api/v1/traces/{trace_id}")
    assert get_res.status_code == 404
    assert test_db_repo.get_by_id(trace_id) is None


def test_delete_trace_cleans_attachment_files_safely(client, test_db_repo, tmp_path):
    """Deleting a trace safely removes its attachment records and owned media files from disk."""
    from app.models.attachment import AttachmentModel
    from app.repositories.attachment_repository import get_attachment_repository
    from app.services.media_storage import get_media_storage

    attach_repo = app.dependency_overrides[get_attachment_repository]()
    storage_svc = app.dependency_overrides[get_media_storage]()

    # 1. Create trace
    create_res = client.post(
        "/api/v1/traces",
        json={
            "observation": "Wild blackberry bush with dark fruit.",
            "latitude": 51.5100,
            "longitude": -0.1200,
            "location_mode": "gps",
        },
    )
    assert create_res.status_code == 201
    trace_id = create_res.json()["id"]

    # 2. Add an attachment file to disk and record
    dummy_file = storage_svc.resolve_safe_path("blackberry_test.jpg")
    dummy_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)

    attach_model = AttachmentModel(
        id="att-test-01",
        trace_id=trace_id,
        media_type="photo",
        stored_filename="blackberry_test.jpg",
        original_filename="blackberry.jpg",
        mime_type="image/jpeg",
        file_size_bytes=24,
        created_at="2026-10-09T12:00:00+00:00",
    )
    attach_repo.create(attach_model)
    assert dummy_file.exists()

    # 3. Delete trace
    del_res = client.delete(f"/api/v1/traces/{trace_id}")
    assert del_res.status_code == 200

    # 4. Confirm attachment record and file are removed
    assert attach_repo.get_by_id("att-test-01") is None
    assert not dummy_file.exists()


def test_two_legitimate_traces_with_identical_titles_remain_distinct(client, test_db_repo):
    """Two legitimate traces with identical titles at different locations or times remain distinct."""
    payload1 = {
        "observation": "Moss Growth on Bricks near the north entrance.",
        "title": "Moss Growth on Bricks",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "location_mode": "gps",
    }
    payload2 = {
        "observation": "Moss Growth on Bricks near the south drain.",
        "title": "Moss Growth on Bricks",
        "latitude": 51.5090,
        "longitude": -0.1290,
        "location_mode": "manual",
    }
    res1 = client.post("/api/v1/traces", json=payload1)
    res2 = client.post("/api/v1/traces", json=payload2)

    assert res1.status_code == 201
    assert res2.status_code == 201
    id1 = res1.json()["id"]
    id2 = res2.json()["id"]
    assert id1 != id2

    list_res = client.get("/api/v1/traces")
    assert list_res.status_code == 200
    ids = [t["id"] for t in list_res.json()]
    assert id1 in ids
    assert id2 in ids


def test_cleanup_duplicate_creation_events(test_db_repo):
    """Cleanup removes duplicate creation events within 10s while keeping separate discoveries."""
    from app.services.trace_service import TraceService
    from app.repositories.attachment_repository import get_attachment_repository
    from app.services.media_storage import get_media_storage

    attach_repo = app.dependency_overrides[get_attachment_repository]()
    storage_svc = app.dependency_overrides[get_media_storage]()
    svc = TraceService(repository=test_db_repo, attachment_repository=attach_repo, media_storage=storage_svc)

    t1 = TraceModel(
        id="trace-dup-01",
        observation="Pigeon nesting in ornamental cornice.",
        category="Nature",
        title="Pigeon Nest",
        summary="Pigeon nesting in cornice.",
        tags=["pigeon"],
        sensory_type="visual",
        confidence=0.9,
        latitude=51.5000,
        longitude=-0.1200,
        location_mode="manual",
        created_at="2026-10-09T10:00:00+00:00",
    )
    # Duplicate created 2 seconds later
    t2 = TraceModel(
        id="trace-dup-02",
        observation="Pigeon nesting in ornamental cornice.",
        category="Nature",
        title="Pigeon Nest",
        summary="Pigeon nesting in cornice.",
        tags=["pigeon"],
        sensory_type="visual",
        confidence=0.9,
        latitude=51.5000,
        longitude=-0.1200,
        location_mode="manual",
        created_at="2026-10-09T10:00:02+00:00",
    )
    # Legitimate separate observation 40 seconds later at different location
    t3 = TraceModel(
        id="trace-separate-03",
        observation="Pigeon nesting in ornamental cornice.",
        category="Nature",
        title="Pigeon Nest",
        summary="Pigeon nesting in cornice.",
        tags=["pigeon"],
        sensory_type="visual",
        confidence=0.9,
        latitude=51.5050,
        longitude=-0.1250,
        location_mode="manual",
        created_at="2026-10-09T10:00:40+00:00",
    )
    test_db_repo.create(t1)
    test_db_repo.create(t2)
    test_db_repo.create(t3)

    cleaned = svc.cleanup_duplicate_creation_events()
    assert cleaned == ["trace-dup-02"]
    assert test_db_repo.get_by_id("trace-dup-01") is not None
    assert test_db_repo.get_by_id("trace-dup-02") is None
    assert test_db_repo.get_by_id("trace-separate-03") is not None


