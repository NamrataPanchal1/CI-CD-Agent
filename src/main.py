"""
AI-CI-CD-Agent — application entrypoint.

Run locally with:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

Or via Docker:
    docker-compose up --build
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from src.api.exception_handlers import register_exception_handlers
from src.api.routers.health import router as health_router
from src.api.routers.repository import router as repository_router
from src.core.config import get_settings
from src.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Application starting",
        extra={
            "extra_fields": {
                "event": "startup",
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "app_env": settings.app_env,
            }
        },
    )
    yield
    logger.info("Application shutting down", extra={"extra_fields": {"event": "shutdown"}})


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered CI/CD automation platform. "
        "Built incrementally, phase by phase — see README.md for the current phase."
    ),
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(repository_router)

register_exception_handlers(app)
