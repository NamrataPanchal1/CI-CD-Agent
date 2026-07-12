"""Response schemas for the health-check endpoint."""
from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Shape of the `GET /health` response."""

    status: str = Field(..., examples=["ok"])
    app_name: str = Field(..., examples=["AI-CI-CD-Agent"])
    version: str = Field(..., examples=["0.1.0"])
    environment: str = Field(..., examples=["development"])
