"""Health-check endpoint.

Purpose:
    Standard liveness/readiness probe. Used locally to confirm the service
    started correctly, and later by container orchestrators (ECS) and load
    balancers to determine instance health.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.dependencies import get_settings_dependency
from src.api.schemas.health import HealthResponse
from src.core.config import Settings
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
def health_check(settings: Settings = Depends(get_settings_dependency)) -> HealthResponse:
    """Return basic liveness information about the running service."""
    logger.info("Health check requested", extra={"extra_fields": {"event": "health_check"}})
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
