"""
Domain-exception -> HTTP-response mapping.

Design decision:
    Route handlers raise domain exceptions (`RepositoryNotFoundError`,
    `GitProviderError`, ...) and never construct `HTTPException`s directly.
    This keeps `application/` and `api/routers/` free of HTTP-specific
    concerns and gives us one place to keep the status-code mapping
    consistent as new domain exceptions are added in later phases.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.logging import get_logger
from src.domain.exceptions import AppException, GitProviderError, RepositoryNotFoundError

logger = get_logger(__name__)

_STATUS_CODE_BY_EXCEPTION: dict[type[AppException], int] = {
    RepositoryNotFoundError: 404,
    GitProviderError: 502,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach a single, generic handler for all `AppException` subclasses."""

    @app.exception_handler(AppException)
    async def handle_app_exception(_: Request, exc: AppException) -> JSONResponse:
        status_code = _STATUS_CODE_BY_EXCEPTION.get(type(exc), 500)

        logger.error(
            "Handled application exception",
            extra={
                "extra_fields": {
                    "event": "app_exception",
                    "error_code": exc.code,
                    "status_code": status_code,
                }
            },
        )

        return JSONResponse(
            status_code=status_code,
            content={"error_code": exc.code, "message": exc.message},
        )
