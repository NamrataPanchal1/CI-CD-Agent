"""
Base domain exceptions.

These exceptions belong to the Domain layer and therefore must never
import anything from FastAPI, boto3, PyGithub, or any other third-party
package. Application and API layers catch these and translate them into
HTTP responses / logs as appropriate.
"""
from __future__ import annotations


class AppException(Exception):
    """Base class for all application-defined exceptions.

    Attributes:
        message: Human-readable explanation of what went wrong.
        code: Short, stable machine-readable error code (e.g. "CONFIG_ERROR").
            Useful for API error responses and log-based alerting/filtering.
    """

    code: str = "APP_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        self.message = message
        if code is not None:
            self.code = code
        super().__init__(self.message)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


class ConfigurationError(AppException):
    """Raised when required configuration/environment variables are missing or invalid."""

    code = "CONFIGURATION_ERROR"


class RepositoryNotFoundError(AppException):
    """Raised when a requested source repository does not exist or is inaccessible."""

    code = "REPOSITORY_NOT_FOUND"


class GitProviderError(AppException):
    """Raised when a git hosting provider (e.g. GitHub) call fails unexpectedly.

    Covers auth failures, rate limiting, network errors, and unexpected
    upstream responses — anything that isn't a clean "not found".
    """

    code = "GIT_PROVIDER_ERROR"
