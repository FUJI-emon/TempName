class LLMServiceError(Exception):
    """Raised when the AI provider fails, times out, or returns malformed data."""


class LLMEmptyInputError(LLMServiceError):
    pass


class LLMInvalidResponseError(LLMServiceError):
    pass