"""TRACE AI API Routes."""
import logging
from fastapi import APIRouter, HTTPException, status

from app.ai.exceptions import (
    AIInvalidResponseError,
    AIParsingError,
    AIServiceUnavailableError,
    AITimeoutError,
)
from app.ai.schemas import AIStatusResponse, TraceAIResult, TraceInterpretRequest
from app.ai.service import ai_service

logger = logging.getLogger("trace.api.ai")

router = APIRouter()


@router.get(
    "/status",
    response_model=AIStatusResponse,
    summary="Check local LM Studio AI service reachability",
    description="Returns whether the configured local LM Studio server is reachable and active.",
)
async def get_ai_status():
    """Probe LM Studio reachability without failing the backend."""
    return await ai_service.get_status()


@router.post(
    "/interpret-trace",
    response_model=TraceAIResult,
    summary="Interpret an observation using local AI",
    description="Classifies a real-world observation into one of the five TRACE categories and generates a structured summary.",
)
async def interpret_trace(request: TraceInterpretRequest):
    """Interpret user observation into structured TRACE discovery."""
    try:
        return await ai_service.interpret_observation(request.observation)
    except AIServiceUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Local AI unavailable",
                "message": "Start LM Studio to interpret this trace.",
            },
        )
    except AITimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error": "TRACE AI took too long to respond.",
                "message": "Try again.",
            },
        )
    except (AIInvalidResponseError, AIParsingError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "TRACE couldn't interpret this observation.",
                "message": "Try describing what you noticed in a little more detail.",
            },
        )
