class LLMConfigurationError(RuntimeError):
    """Raised when the LLM provider is not configured correctly."""


class LLMResponseError(RuntimeError):
    """Raised when the LLM returns missing or invalid content."""


class QueryExecutionConfigurationError(RuntimeError):
    """Raised when read-only query execution is not configured."""


class QueryRejectedError(RuntimeError):
    """Raised when static guardrails reject submitted SQL."""

    def __init__(
        self,
        message: str,
        guardrail: object,
    ) -> None:
        super().__init__(message)
        self.guardrail = guardrail


class QueryPlanRejectedError(RuntimeError):
    """Raised when EXPLAIN estimates exceed safety limits."""

    def __init__(
        self,
        message: str,
        explain: object,
    ) -> None:
        super().__init__(message)
        self.explain = explain


class QueryTimeoutError(RuntimeError):
    """Raised when PostgreSQL cancels a slow query."""


class QueryExecutionError(RuntimeError):
    """Raised when approved SQL cannot be executed."""

class AuthenticationConfigurationError(RuntimeError):
    """Raised when authentication settings are missing."""


class EmailAlreadyRegisteredError(RuntimeError):
    """Raised when an email address already exists."""


class InvalidCredentialsError(RuntimeError):
    """Raised when login credentials are incorrect."""


class InvalidTokenError(RuntimeError):
    """Raised when an access token cannot be validated."""


class InactiveUserError(RuntimeError):
    """Raised when an inactive account tries to authenticate."""    