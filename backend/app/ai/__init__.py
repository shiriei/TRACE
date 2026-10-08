"""TRACE AI Module Package."""
from app.ai.client import LMStudioClient
from app.ai.exceptions import (
    AIError,
    AIInvalidResponseError,
    AIParsingError,
    AIServiceUnavailableError,
    AITimeoutError,
)
from app.ai.schemas import (
    AIStatusResponse,
    SensoryType,
    TraceAIResult,
    TraceCategory,
    TraceInterpretRequest,
)
from app.ai.service import TraceAIService, ai_service

__all__ = [
    "AIError",
    "AIServiceUnavailableError",
    "AITimeoutError",
    "AIInvalidResponseError",
    "AIParsingError",
    "TraceCategory",
    "SensoryType",
    "TraceInterpretRequest",
    "TraceAIResult",
    "AIStatusResponse",
    "LMStudioClient",
    "TraceAIService",
    "ai_service",
]
