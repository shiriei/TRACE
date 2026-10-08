"""TRACE AI Domain Exceptions."""


class AIError(Exception):
    """Base exception for TRACE AI operations."""

    def __init__(self, message: str, code: str = "AI_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class AIServiceUnavailableError(AIError):
    """Raised when LM Studio endpoint cannot be reached."""

    def __init__(
        self,
        message: str = "Local AI unavailable. Start LM Studio to interpret this trace.",
    ):
        super().__init__(message=message, code="AI_UNAVAILABLE")


class AITimeoutError(AIError):
    """Raised when LM Studio request times out."""

    def __init__(
        self,
        message: str = "TRACE AI took too long to respond. Try again.",
    ):
        super().__init__(message=message, code="AI_TIMEOUT")


class AIInvalidResponseError(AIError):
    """Raised when LM Studio returns an unexpected HTTP status or error."""

    def __init__(
        self,
        message: str = "TRACE couldn't interpret this observation. Try describing what you noticed in a little more detail.",
    ):
        super().__init__(message=message, code="AI_INVALID_RESPONSE")


class AIParsingError(AIError):
    """Raised when model response cannot be parsed into structured TraceAIResult."""

    def __init__(
        self,
        message: str = "TRACE couldn't interpret this observation. Try describing what you noticed in a little more detail.",
    ):
        super().__init__(message=message, code="AI_PARSING_ERROR")
