"""Shared pytest fixtures for the test suite."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture()
def client() -> TestClient:
    """A FastAPI test client bound to the application instance."""
    return TestClient(app)
