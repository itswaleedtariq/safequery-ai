class LLMConfigurationError(RuntimeError):
    """Raised when the LLM provider is not configured correctly."""


class LLMResponseError(RuntimeError):
    """Raised when the LLM returns missing or invalid content."""