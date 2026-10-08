"""TRACE AI Service Layer coordinating model inference and structured output parsing."""
import json
import logging
import re
from typing import Optional
from pydantic import ValidationError

from app.ai.client import LMStudioClient
from app.ai.exceptions import AIParsingError
from app.ai.prompts import (
    TRACE_AI_JSON_SCHEMA,
    build_interpretation_messages,
)
from app.ai.schemas import AIStatusResponse, TraceAIResult
from app.core.config import settings

logger = logging.getLogger("trace.ai.service")


def _extract_and_validate_json(raw_content: str) -> TraceAIResult:
    """Extract and validate JSON content from LLM response into TraceAIResult."""
    content = raw_content.strip()

    # Strip markdown code blocks if the model wrapped the output in ```json ... ```
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if code_block_match:
        content = code_block_match.group(1).strip()

    # Attempt to locate first { and last } if stray characters surround the object
    first_brace = content.find("{")
    last_brace = content.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        content = content[first_brace : last_brace + 1]

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning("Failed to decode model JSON: %s. Raw: %s", str(e), raw_content[:200])
        raise AIParsingError() from e

    try:
        return TraceAIResult.model_validate(data)
    except ValidationError as e:
        logger.warning("TraceAIResult schema validation failed: %s. Data: %s", str(e), data)
        raise AIParsingError() from e


class TraceAIService:
    """High-level service for TRACE AI interpretation."""

    def __init__(self, client: Optional[LMStudioClient] = None):
        self.client = client or LMStudioClient()

    async def get_status(self) -> AIStatusResponse:
        """Probe configured LM Studio status and return availability."""
        is_available = await self.client.check_availability()
        return AIStatusResponse(
            available=is_available,
            provider="lm-studio",
            model=self.client.model,
        )

    async def interpret_observation(self, observation: str) -> TraceAIResult:
        """Interpret a real-world observation into a structured TraceAIResult.

        Performs one controlled retry if the initial model output is malformed.
        """
        clean_obs = observation.strip()
        messages = build_interpretation_messages(clean_obs)

        # Attempt 1
        raw_result = await self.client.generate_chat_completion(
            messages=messages,
            response_format=TRACE_AI_JSON_SCHEMA,
            temperature=0.2,
        )

        try:
            return _extract_and_validate_json(raw_result)
        except AIParsingError:
            logger.info("Attempt 1 produced malformed output. Retrying once with strict reminder...")

        # Controlled Retry Attempt
        retry_messages = list(messages)
        retry_messages.append({"role": "assistant", "content": raw_result})
        retry_messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous response was not valid JSON conforming to the requested schema. "
                    "Respond with ONLY a raw JSON object containing category, title, summary, tags, "
                    "sensory_type, and confidence."
                ),
            }
        )

        retry_raw = await self.client.generate_chat_completion(
            messages=retry_messages,
            response_format=TRACE_AI_JSON_SCHEMA,
            temperature=0.1,
        )

        return _extract_and_validate_json(retry_raw)


# Shared service singleton
ai_service = TraceAIService()
