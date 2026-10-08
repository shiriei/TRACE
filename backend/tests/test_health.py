from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that the service entrypoint responds with status 200 and valid metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "TRACE"
    assert data["status"] == "online"
    assert "version" in data
    assert data["health"] == "/health"


def test_health_endpoint():
    """Verify that /health returns 200 and matches the HealthResponse schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "TRACE"
    assert "version" in data
    assert "timestamp" in data
    assert "environment" in data


def test_versioned_health_endpoint():
    """Verify that /api/v1/health also returns 200 and matches the HealthResponse schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "TRACE"
