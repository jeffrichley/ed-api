"""Exception classes for ed-api."""


class EdAPIError(Exception):
    """Base exception for all Ed API errors."""

    def __init__(self, message: str, status_code: int, response_body: dict):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class EdAuthError(EdAPIError):
    """Authentication failed (401)."""


class EdForbiddenError(EdAPIError):
    """Insufficient permissions (403)."""


class EdNotFoundError(EdAPIError):
    """Resource not found (404)."""


class EdRateLimitError(EdAPIError):
    """Rate limited (429)."""
