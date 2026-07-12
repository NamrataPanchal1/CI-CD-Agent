"""Unit tests for the /health endpoint."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape(client: TestClient) -> None:
    response = client.get("/health")
    body = response.json()

    assert body["status"] == "ok"
    assert body["app_name"]
    assert body["version"]
    assert body["environment"] in {"development", "staging", "production", "test"}
