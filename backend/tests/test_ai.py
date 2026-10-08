"""Unit and Integration tests for TRACE Local AI Architecture."""
import json
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.ai.exceptions import (
    AIInvalidResponseError,
    AIParsingError,
    AIServiceUnavailableError,
    AITimeoutError,
)
from app.ai.schemas import (
    AIStatusResponse,
    TraceAIResult,
    TraceCategory,
    TraceInterpretRequest,
)
from app.ai.service import TraceAIService
from app.main import app

client = TestClient(app)

SAMPLE_VALID_AI_PAYLOAD = {
    "category": "Nature",
    "title": "Moss between the old bricks",
    "summary": "Green moss is growing in the damp gap between the bricks beside the drain.",
    "tags": ["moss", "bricks", "drain"],
    "sensory_type": "visual",
    "confidence": 0.95,
}


# =====================================================================
# 1. Schema Validation Tests
# =====================================================================

def test_each_of_five_categories_accepted():
    """Verify that all 5 canonical TRACE categories are accepted by the schema."""
    categories: list[TraceCategory] = ["Nature", "Sound", "Structure", "Mystery", "Personal"]
    for cat in categories:
        data = {**SAMPLE_VALID_AI_PAYLOAD, "category": cat}
        result = TraceAIResult.model_validate(data)
        assert result.category == cat


def test_invalid_category_rejected():
    """Verify that arbitrary or unapproved categories are strictly rejected."""
    invalid_categories = ["Technology", "Urban", "Social", "Random", ""]
    for cat in invalid_categories:
        with pytest.raises(ValidationError):
            TraceAIResult.model_validate({**SAMPLE_VALID_AI_PAYLOAD, "category": cat})


def test_invalid_confidence_rejected():
    """Verify that confidence score must be strictly between 0.0 and 1.0."""
    invalid_confidences = [-0.1, 1.05, 2.0, -100.0]
    for conf in invalid_confidences:
        with pytest.raises(ValidationError):
            TraceAIResult.model_validate({**SAMPLE_VALID_AI_PAYLOAD, "confidence": conf})

    # Edge cases 0.0 and 1.0 must be accepted
    res_zero = TraceAIResult.model_validate({**SAMPLE_VALID_AI_PAYLOAD, "confidence": 0.0})
    assert res_zero.confidence == 0.0

    res_one = TraceAIResult.model_validate({**SAMPLE_VALID_AI_PAYLOAD, "confidence": 1.0})
    assert res_one.confidence == 1.0


def test_invalid_sensory_type_rejected():
    """Verify that sensory_type must be one of the controlled values."""
    with pytest.raises(ValidationError):
        TraceAIResult.model_validate({**SAMPLE_VALID_AI_PAYLOAD, "sensory_type": "telepathic"})


def test_empty_observation_rejected():
    """Verify that empty or whitespace-only observations are rejected."""
    with pytest.raises(ValidationError):
        TraceInterpretRequest(observation="   ")


# =====================================================================
# 2. Service Unit Tests
# =====================================================================

@pytest.mark.anyio
async def test_service_successful_interpretation():
    """Service successfully parses valid JSON response from client."""
    mock_client = AsyncMock()
    mock_client.generate_chat_completion.return_value = json.dumps(SAMPLE_VALID_AI_PAYLOAD)

    service = TraceAIService(client=mock_client)
    result = await service.interpret_observation("I noticed moss between bricks.")

    assert isinstance(result, TraceAIResult)
    assert result.category == "Nature"
    assert result.title == "Moss between the old bricks"
    assert "moss" in result.tags


@pytest.mark.anyio
async def test_service_handles_markdown_codeblock():
    """Service cleans and validates response wrapped in ```json ... ``` blocks."""
    wrapped_json = f"```json\n{json.dumps(SAMPLE_VALID_AI_PAYLOAD)}\n```"
    mock_client = AsyncMock()
    mock_client.generate_chat_completion.return_value = wrapped_json

    service = TraceAIService(client=mock_client)
    result = await service.interpret_observation("I noticed moss.")

    assert result.category == "Nature"


@pytest.mark.anyio
async def test_service_retry_on_malformed_initial_response():
    """Service retries once when initial attempt is malformed and succeeds on second attempt."""
    mock_client = AsyncMock()
    # First call returns non-json text, second call returns valid json
    mock_client.generate_chat_completion.side_effect = [
        "Sure, here is your interpretation: not json!",
        json.dumps(SAMPLE_VALID_AI_PAYLOAD),
    ]

    service = TraceAIService(client=mock_client)
    result = await service.interpret_observation("I noticed moss.")

    assert mock_client.generate_chat_completion.call_count == 2
    assert result.category == "Nature"


@pytest.mark.anyio
async def test_service_raises_parsing_error_when_all_attempts_malformed():
    """Service raises AIParsingError when all attempts return invalid JSON."""
    mock_client = AsyncMock()
    mock_client.generate_chat_completion.return_value = "Sorry, I cannot answer in JSON."

    service = TraceAIService(client=mock_client)
    with pytest.raises(AIParsingError):
        await service.interpret_observation("I noticed moss.")


# =====================================================================
# 3. HTTP API Endpoint Tests
# =====================================================================

def test_api_status_available():
    """GET /api/v1/ai/status reports available=true when probe succeeds."""
    with patch("app.api.routes.ai.ai_service.get_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = AIStatusResponse(
            available=True,
            provider="lm-studio",
            model="google/gemma-3-4b",
        )
        response = client.get("/api/v1/ai/status")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert data["provider"] == "lm-studio"
        assert data["model"] == "google/gemma-3-4b"


def test_api_status_unavailable_does_not_fail_server():
    """GET /api/v1/ai/status returns available=false gracefully without server failure."""
    with patch("app.api.routes.ai.ai_service.get_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = AIStatusResponse(
            available=False,
            provider="lm-studio",
            model="google/gemma-3-4b",
        )
        response = client.get("/api/v1/ai/status")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert data["provider"] == "lm-studio"


def test_api_interpret_trace_valid_observation():
    """POST /api/v1/ai/interpret-trace returns structured result for valid observation."""
    with patch("app.api.routes.ai.ai_service.interpret_observation", new_callable=AsyncMock) as mock_interpret:
        mock_interpret.return_value = TraceAIResult.model_validate(SAMPLE_VALID_AI_PAYLOAD)

        response = client.post(
            "/api/v1/ai/interpret-trace",
            json={"observation": "Green moss is growing between old bricks beside a drain."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Nature"
        assert data["title"] == "Moss between the old bricks"
        assert "moss" in data["tags"]
        assert data["sensory_type"] == "visual"
        assert data["confidence"] == 0.95


def test_api_interpret_trace_service_unavailable():
    """POST /api/v1/ai/interpret-trace returns 503 when LM Studio is unreachable."""
    with patch("app.api.routes.ai.ai_service.interpret_observation", new_callable=AsyncMock) as mock_interpret:
        mock_interpret.side_effect = AIServiceUnavailableError()

        response = client.post(
            "/api/v1/ai/interpret-trace",
            json={"observation": "I heard an echo in the subway tunnel."},
        )
        assert response.status_code == 503
        data = response.json()
        assert "Local AI unavailable" in data["detail"]["error"]
        assert "Start LM Studio" in data["detail"]["message"]


def test_api_interpret_trace_timeout():
    """POST /api/v1/ai/interpret-trace returns 504 on model timeout."""
    with patch("app.api.routes.ai.ai_service.interpret_observation", new_callable=AsyncMock) as mock_interpret:
        mock_interpret.side_effect = AITimeoutError()

        response = client.post(
            "/api/v1/ai/interpret-trace",
            json={"observation": "I heard an echo in the tunnel."},
        )
        assert response.status_code == 504
        data = response.json()
        assert "TRACE AI took too long to respond" in data["detail"]["error"]
        assert "Try again" in data["detail"]["message"]


def test_api_interpret_trace_malformed_response():
    """POST /api/v1/ai/interpret-trace returns 502 on invalid model response."""
    with patch("app.api.routes.ai.ai_service.interpret_observation", new_callable=AsyncMock) as mock_interpret:
        mock_interpret.side_effect = AIParsingError()

        response = client.post(
            "/api/v1/ai/interpret-trace",
            json={"observation": "I heard an echo in the tunnel."},
        )
        assert response.status_code == 502
        data = response.json()
        assert "couldn't interpret this observation" in data["detail"]["error"]


def test_api_interpret_trace_validation_error():
    """POST /api/v1/ai/interpret-trace returns 422 for empty or invalid observation payload."""
    response = client.post(
        "/api/v1/ai/interpret-trace",
        json={"observation": ""},
    )
    assert response.status_code == 422
