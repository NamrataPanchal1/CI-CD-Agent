"""
Application-wide structured logging.

Design decision:
    Every module logs through `get_logger(__name__)` instead of `print()`,
    giving us consistent, filterable, and (in production) JSON-formatted
    logs from Phase 1 onward. JSON logs are important because later phases
    will ship this app in containers on ECS/CloudWatch, where structured
    logs are far easier to query and alert on than free-text lines.

    Format is controlled by the `LOG_FORMAT` env var:
      - "json": one JSON object per line (recommended for staging/production)
      - "text": human-readable, col300-free format (convenient for local dev)
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from src.core.config import get_settings

_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Allow callers to attach structured context via `extra={"extra_fields": {...}}`
        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            payload.update(extra_fields)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure the root logger exactly once per process.

    Safe to call multiple times; subsequent calls are no-ops. This is
    invoked at application startup (see `src/main.py`).
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()

    handler = logging.StreamHandler(stream=sys.stdout)
    if settings.log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)

    # Keep noisy third-party loggers at a sane level.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger. Ensures logging is configured first."""
    configure_logging()
    return logging.getLogger(name)
