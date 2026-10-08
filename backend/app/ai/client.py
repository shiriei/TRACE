"""Isolated HTTP client for communication with local LM Studio OpenAI-compatible endpoint."""
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.ai.exceptions import (
    AIInvalidResponseError,
    AIServiceUnavailableError,
    AITimeoutError,
)
from app.core.config import settings

logger = logging.getLogger("trace.ai.client")


class LMStudioClient:
    """Client for local LM Studio OpenAI-compatible Chat Completions API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.LM_STUDIO_BASE_URL).rstrip("/")
        self.model = model or settings.LM_STUDIO_MODEL
        self.api_key = api_key or settings.LM_STUDIO_API_KEY
        self.timeout = timeout if timeout is not None else settings.LM_STUDIO_TIMEOUT_SECONDS

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def check_availability(self) -> bool:
        """Probe the LM Studio models endpoint to verify server reachability."""
        url = f"{self.base_url}/models"
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                response = await client.get(url, headers=self._get_headers())
                return response.status_code == 200
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException):
            return False
        except Exception as e:
            logger.debug("LM Studio availability probe encountered error: %s", str(e))
            return False

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> str:
        """Send chat completion request to local LM Studio endpoint.

        Returns raw assistant response content string.
        Raises AIServiceUnavailableError, AITimeoutError, or AIInvalidResponseError.
        """
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if response_format:
            payload["response_format"] = response_format

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=self._get_headers())

            if response.status_code != 200:
                logger.warning(
                    "LM Studio responded with HTTP %d: %s",
                    response.status_code,
                    response.text[:300],
                )
                raise AIInvalidResponseError(
                    f"LM Studio returned status {response.status_code}"
                )

            data = response.json()
            choices = data.get("choices")
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                raise AIInvalidResponseError("Empty choices list received from local model")

            message = choices[0].get("message", {})
            content = message.get("content")
            if content is None:
                raise AIInvalidResponseError("No message content received from local model")

            return str(content)

        except (httpx.ConnectError, httpx.NetworkError) as e:
            logger.warning("Could not connect to LM Studio at %s: %s", self.base_url, str(e))
            raise AIServiceUnavailableError()
        except (httpx.TimeoutException, httpx.ReadTimeout) as e:
            logger.warning("Timeout waiting for LM Studio response at %s: %s", url, str(e))
            raise AITimeoutError()
        except (AIServiceUnavailableError, AITimeoutError, AIInvalidResponseError):
            raise
        except Exception as e:
            logger.error("Unexpected error communicating with LM Studio: %s", str(e), exc_info=True)
            raise AIInvalidResponseError(f"Unexpected local AI client error: {str(e)}")
