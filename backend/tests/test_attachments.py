"""Tests for TRACE Local Media Storage and Attachment Endpoints."""
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.ai.schemas import TraceAIResult
from app.db.database import SQLiteDatabase
from app.main import app
from app.models.attachment import AttachmentModel
from app.models.trace import TraceModel
from app.repositories.attachment_repository import (
    AttachmentRepository,
    get_attachment_repository,
)
from app.repositories.trace_repository import (
    TraceRepository,
    get_trace_repository,
)
from app.services.media_storage import (
    FileTooLargeError,
    MediaStorageService,
    PathTraversalError,
    UnsupportedMediaTypeError,
    get_media_storage,
    sniff_media_type,
)

# Binary fixtures for real valid formats
JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
    b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
    b"\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01"
    b"\x00\x01\x01\x01\x11\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
)

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00"
    b"\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

WAV_BYTES = (
    b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00"
    b"\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
)

MP3_BYTES = b"ID3\x03\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x44\x00\x00\x00\x00"


@pytest.fixture
def test_env(tmp_path):
    """Provides isolated SQLite database, repositories, and media storage directory."""
    db_file = tmp_path / "test_traces.db"
    media_dir = tmp_path / "test_media"
    media_dir.mkdir(exist_ok=True)

    db_instance = SQLiteDatabase(db_path=str(db_file))
    trace_repo = TraceRepository(database=db_instance)
    attach_repo = AttachmentRepository(database=db_instance)
    storage_svc = MediaStorageService(
        media_dir=str(media_dir),
        max_upload_size=2 * 1024 * 1024,  # 2 MB for tests
    )

    app.dependency_overrides[get_trace_repository] = lambda: trace_repo
    app.dependency_overrides[get_attachment_repository] = lambda: attach_repo
    app.dependency_overrides[get_media_storage] = lambda: storage_svc

    yield {
        "db": db_instance,
        "trace_repo": trace_repo,
        "attach_repo": attach_repo,
        "storage": storage_svc,
        "media_dir": media_dir,
    }

    app.dependency_overrides.pop(get_trace_repository, None)
    app.dependency_overrides.pop(get_attachment_repository, None)
    app.dependency_overrides.pop(get_media_storage, None)


@pytest.fixture(autouse=True)
def mock_default_ai():
    """Default AI mock so tests execute instantly without real network calls."""
    default_result = TraceAIResult(
        category="Nature",
        title="Field Observation",
        summary="A notable observation in the physical surroundings.",
        tags=["field", "nature"],
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
def client(test_env):
    """Test client bound to isolated test environment."""
    return TestClient(app)


def _create_trace(client, observation="Test observation") -> str:
    """Helper to create a trace and return its ID."""
    res = client.post(
        "/api/v1/traces",
        json={
            "observation": observation,
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location_mode": "gps",
        },
    )
    assert res.status_code == 201
    return res.json()["id"]


# =====================================================================
# 1. Upload valid photo & audio
# =====================================================================

def test_upload_valid_photo(client, test_env):
    """Upload a valid photo attachment and verify returned metadata and storage."""
    trace_id = _create_trace(client, "Old mossy stone steps leading nowhere.")

    response = client.post(
        f"/api/v1/traces/{trace_id}/attachments",
        files={"file": ("mossy_steps.jpg", JPEG_BYTES, "image/jpeg")},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["id"].startswith("attach-")
    assert data["trace_id"] == trace_id
    assert data["media_type"] == "photo"
    assert data["mime_type"] == "image/jpeg"
    assert data["original_filename"] == "mossy_steps.jpg"
    assert data["file_size_bytes"] == len(JPEG_BYTES)
    assert data["stored_filename"].endswith(".jpg")
    # Verify no local filesystem absolute paths are leaked
    assert "/" not in data["stored_filename"]
    assert "\\" not in data["stored_filename"]
    assert ":" not in data["stored_filename"]

    # Verify physical file exists in isolated media directory
    stored_path = test_env["media_dir"] / data["stored_filename"]
    assert stored_path.exists()
    assert stored_path.read_bytes() == JPEG_BYTES


def test_upload_valid_audio(client, test_env):
    """Upload a valid audio attachment and verify returned metadata and storage."""
    trace_id = _create_trace(client, "Evening cicada hum by the river.")

    response = client.post(
        f"/api/v1/traces/{trace_id}/attachments",
        files={"file": ("cicadas.wav", WAV_BYTES, "audio/wav")},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["id"].startswith("attach-")
    assert data["trace_id"] == trace_id
    assert data["media_type"] == "audio"
    assert data["mime_type"] == "audio/wav"
    assert data["original_filename"] == "cicadas.wav"
    assert data["file_size_bytes"] == len(WAV_BYTES)
    assert data["stored_filename"].endswith(".wav")

    stored_path = test_env["media_dir"] / data["stored_filename"]
    assert stored_path.exists()
    assert stored_path.read_bytes() == WAV_BYTES


# =====================================================================
# 2. Reject unsupported file types & spoofed content
# =====================================================================

def test_reject_unsupported_file_types(client, test_env):
    """Reject non-photo/audio files such as text files or shell scripts."""
    trace_id = _create_trace(client)

    # Disguised text file
    response = client.post(
        f"/api/v1/traces/{trace_id}/attachments",
        files={"file": ("notes.txt", b"plain text content that is not media", "text/plain")},
    )
    assert response.status_code == 415
    assert "unsupported" in response.json()["detail"].lower()

    # Script named with .jpg extension (MIME spoofing)
    response_spoofed = client.post(
        f"/api/v1/traces/{trace_id}/attachments",
        files={"file": ("malicious.jpg", b"#!/bin/bash\necho hello\n", "image/jpeg")},
    )
    assert response_spoofed.status_code == 415

    # Verify nothing was saved in media directory
    files_in_media = list(test_env["media_dir"].iterdir())
    assert len(files_in_media) == 0


def test_reject_empty_file(client, test_env):
    """Reject 0-byte uploads."""
    trace_id = _create_trace(client)

    response = client.post(
        f"/api/v1/traces/{trace_id}/attachments",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 415
    assert "empty" in response.json()["detail"].lower()


# =====================================================================
# 3. Reject oversized files and clean up partial files
# =====================================================================

def test_reject_oversized_files_and_cleanup_partials(client, test_env):
    """Reject files exceeding max_upload_size and ensure no partial files remain on disk."""
    trace_id = _create_trace(client)

    # test_env has max_upload_size configured to 2 MB
    # Create a JPEG payload larger than 2 MB
    oversized_bytes = JPEG_BYTES + (b"\x00" * (2 * 1024 * 1024 + 500))

    response = client.post(
        f"/api/v1/traces/{trace_id}/attachments",
        files={"file": ("huge_photo.jpg", oversized_bytes, "image/jpeg")},
    )

    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"].lower()

    # Crucial safeguard: no partial files left in storage
    files_in_media = list(test_env["media_dir"].iterdir())
    assert len(files_in_media) == 0


# =====================================================================
# 4. Reject uploads for nonexistent traces
# =====================================================================

def test_reject_upload_for_nonexistent_trace(client, test_env):
    """Uploads for nonexistent traces return 404 and write no files to disk."""
    fake_trace_id = "trace-nonexistent-12345"

    response = client.post(
        f"/api/v1/traces/{fake_trace_id}/attachments",
        files={"file": ("photo.jpg", JPEG_BYTES, "image/jpeg")},
    )

    assert response.status_code == 404
    assert fake_trace_id in response.json()["detail"]

    # Verify no orphaned file was created
    assert len(list(test_env["media_dir"].iterdir())) == 0


# =====================================================================
# 5. List attachments for a trace
# =====================================================================

def test_list_attachments_for_trace(client):
    """List attachments belonging to a trace, partitioned per trace."""
    trace_1 = _create_trace(client, "Trace 1")
    trace_2 = _create_trace(client, "Trace 2")

    # Upload 2 attachments to Trace 1
    res1 = client.post(
        f"/api/v1/traces/{trace_1}/attachments",
        files={"file": ("photo1.jpg", JPEG_BYTES, "image/jpeg")},
    )
    res2 = client.post(
        f"/api/v1/traces/{trace_1}/attachments",
        files={"file": ("audio1.wav", WAV_BYTES, "audio/wav")},
    )
    # Upload 1 attachment to Trace 2
    res3 = client.post(
        f"/api/v1/traces/{trace_2}/attachments",
        files={"file": ("photo2.png", PNG_BYTES, "image/png")},
    )

    # Check Trace 1
    list1_res = client.get(f"/api/v1/traces/{trace_1}/attachments")
    assert list1_res.status_code == 200
    list1 = list1_res.json()
    assert len(list1) == 2
    assert {a["id"] for a in list1} == {res1.json()["id"], res2.json()["id"]}
    assert all(a["trace_id"] == trace_1 for a in list1)

    # Check Trace 2
    list2_res = client.get(f"/api/v1/traces/{trace_2}/attachments")
    assert list2_res.status_code == 200
    list2 = list2_res.json()
    assert len(list2) == 1
    assert list2[0]["id"] == res3.json()["id"]
    assert list2[0]["trace_id"] == trace_2

    # Check nonexistent trace returns 404
    assert client.get("/api/v1/traces/does-not-exist/attachments").status_code == 404


# =====================================================================
# 6. Retrieve attachment metadata and content
# =====================================================================

def test_retrieve_attachment_metadata_and_content(client):
    """Retrieve attachment metadata and stream its raw binary contents."""
    trace_id = _create_trace(client)

    upload_res = client.post(
        f"/api/v1/traces/{trace_id}/attachments",
        files={"file": ("sample.png", PNG_BYTES, "image/png")},
    )
    assert upload_res.status_code == 201
    att_id = upload_res.json()["id"]

    # Metadata endpoint
    meta_res = client.get(f"/api/v1/traces/{trace_id}/attachments/{att_id}")
    assert meta_res.status_code == 200
    assert meta_res.json()["id"] == att_id
    assert meta_res.json()["media_type"] == "photo"
    assert meta_res.json()["mime_type"] == "image/png"

    # Content streaming endpoint
    content_res = client.get(f"/api/v1/traces/{trace_id}/attachments/{att_id}/content")
    assert content_res.status_code == 200
    assert content_res.headers["content-type"] == "image/png"
    assert content_res.content == PNG_BYTES

    # Nonexistent attachment content returns 404
    assert client.get(f"/api/v1/traces/{trace_id}/attachments/nonexistent/content").status_code == 404


# =====================================================================
# 7. Delete attachment and stored file safely
# =====================================================================

def test_delete_attachment_and_stored_file(client, test_env):
    """Delete an attachment, verifying its database record and on-disk file are deleted."""
    trace_id = _create_trace(client)

    upload_res = client.post(
        f"/api/v1/traces/{trace_id}/attachments",
        files={"file": ("photo.jpg", JPEG_BYTES, "image/jpeg")},
    )
    att_data = upload_res.json()
    att_id = att_data["id"]
    stored_name = att_data["stored_filename"]
    stored_path = test_env["media_dir"] / stored_name

    assert stored_path.exists()

    # Delete attachment
    del_res = client.delete(f"/api/v1/traces/{trace_id}/attachments/{att_id}")
    assert del_res.status_code == 200
    assert del_res.json()["id"] == att_id

    # Verify file was deleted from disk
    assert not stored_path.exists()

    # Verify metadata cannot be fetched
    assert client.get(f"/api/v1/traces/{trace_id}/attachments/{att_id}").status_code == 404
    # Verify content cannot be fetched
    assert client.get(f"/api/v1/traces/{trace_id}/attachments/{att_id}/content").status_code == 404
    # Second delete returns 404
    assert client.delete(f"/api/v1/traces/{trace_id}/attachments/{att_id}").status_code == 404


# =====================================================================
# 8. Delete trace containing attachments (cascade cleanup)
# =====================================================================

def test_delete_trace_cleans_up_all_attachment_files(client, test_env):
    """Deleting a trace cleans up all associated attachment files and database records."""
    trace_id = _create_trace(client)

    # Attach photo and audio
    res_photo = client.post(
        f"/api/v1/traces/{trace_id}/attachments",
        files={"file": ("photo.jpg", JPEG_BYTES, "image/jpeg")},
    ).json()
    res_audio = client.post(
        f"/api/v1/traces/{trace_id}/attachments",
        files={"file": ("audio.mp3", MP3_BYTES, "audio/mpeg")},
    ).json()

    photo_path = test_env["media_dir"] / res_photo["stored_filename"]
    audio_path = test_env["media_dir"] / res_audio["stored_filename"]
    assert photo_path.exists()
    assert audio_path.exists()

    # Delete trace
    del_trace_res = client.delete(f"/api/v1/traces/{trace_id}")
    assert del_trace_res.status_code == 200

    # Verify both physical files have been deleted from disk
    assert not photo_path.exists()
    assert not audio_path.exists()

    # Verify database attachments table has no orphaned rows
    attachments_in_db = test_env["attach_repo"].get_by_trace_id(trace_id)
    assert len(attachments_in_db) == 0


# =====================================================================
# 9. Prevent unsafe filenames and path traversal
# =====================================================================

def test_prevent_unsafe_filenames_and_path_traversal(client, test_env):
    """Malicious filenames in uploads do not dictate stored file paths and path traversal is blocked."""
    trace_id = _create_trace(client)

    # Malicious filenames supplied by client
    malicious_names = [
        "../../etc/passwd.jpg",
        "..\\..\\windows\\system32.jpg",
        "/absolute/path/file.jpg",
        "foo/bar/test.jpg",
    ]

    for bad_name in malicious_names:
        res = client.post(
            f"/api/v1/traces/{trace_id}/attachments",
            files={"file": (bad_name, JPEG_BYTES, "image/jpeg")},
        )
        assert res.status_code == 201
        data = res.json()
        stored_name = data["stored_filename"]

        # Filename on disk is strictly random UUID without path separators
        assert "/" not in stored_name
        assert "\\" not in stored_name
        assert ".." not in stored_name

        # Ensure file is inside media_dir
        actual_file = test_env["media_dir"] / stored_name
        assert actual_file.exists()

    # Test MediaStorageService.resolve_safe_path directly
    storage: MediaStorageService = test_env["storage"]
    with pytest.raises(PathTraversalError):
        storage.resolve_safe_path("../../secret.txt")

    with pytest.raises(PathTraversalError):
        storage.resolve_safe_path("..\\evil.txt")

    with pytest.raises(PathTraversalError):
        storage.resolve_safe_path("sub/dir/file.txt")

    # Safe delete cannot delete outside media_dir
    assert storage.delete_file("../../any_system_file") is False


# =====================================================================
# 10. Persistence across application restarts
# =====================================================================

def test_attachment_persistence_across_sessions(tmp_path):
    """Attachments and media persist intact across application and DB restarts."""
    db_file = tmp_path / "persistent_traces.db"
    media_dir = tmp_path / "persistent_media"
    media_dir.mkdir()

    # Session 1: Create trace and attachment
    db1 = SQLiteDatabase(db_path=str(db_file))
    trace_repo1 = TraceRepository(database=db1)
    attach_repo1 = AttachmentRepository(database=db1)
    storage1 = MediaStorageService(media_dir=str(media_dir))

    trace = TraceModel(
        id="trace-persist-01",
        observation="Ancient sundial marker in courtyard.",
        category="Mystery",
        title="Ancient Sundial Marker",
        summary="A stone sundial marker in the courtyard.",
        tags=["sundial", "courtyard"],
        sensory_type="visual",
        confidence=0.9,
        created_at="2026-10-09T03:00:00Z",
    )
    trace_repo1.create(trace)

    unique_filename = storage1.generate_stored_filename("jpg")
    file_path = storage1.resolve_safe_path(unique_filename)
    file_path.write_bytes(JPEG_BYTES)

    attachment = AttachmentModel(
        id="attach-persist-01",
        trace_id="trace-persist-01",
        media_type="photo",
        stored_filename=unique_filename,
        original_filename="sundial.jpg",
        mime_type="image/jpeg",
        file_size_bytes=len(JPEG_BYTES),
        created_at="2026-10-09T03:00:05Z",
    )
    attach_repo1.create(attachment)

    # Terminate Session 1
    del attach_repo1
    del trace_repo1
    del db1
    del storage1

    # Session 2: Connect anew
    db2 = SQLiteDatabase(db_path=str(db_file))
    trace_repo2 = TraceRepository(database=db2)
    attach_repo2 = AttachmentRepository(database=db2)
    storage2 = MediaStorageService(media_dir=str(media_dir))

    loaded_trace = trace_repo2.get_by_id("trace-persist-01")
    assert loaded_trace is not None
    assert loaded_trace.title == "Ancient Sundial Marker"

    loaded_att = attach_repo2.get_by_id("attach-persist-01")
    assert loaded_att is not None
    assert loaded_att.id == "attach-persist-01"
    assert loaded_att.trace_id == "trace-persist-01"
    assert loaded_att.original_filename == "sundial.jpg"
    assert loaded_att.stored_filename == unique_filename
    assert loaded_att.file_size_bytes == len(JPEG_BYTES)

    # Verify on-disk file remains readable and uncorrupted
    retrieved_path = storage2.get_file_path(loaded_att.stored_filename)
    assert retrieved_path.exists()
    assert retrieved_path.read_bytes() == JPEG_BYTES
