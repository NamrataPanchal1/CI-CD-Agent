"""Tests for the `GET /repos/{owner}/{name}` and `.../analysis` endpoints.

The use-case dependencies are overridden with fakes so these tests never
make real HTTP calls to GitHub and don't require a `GITHUB_TOKEN` to be set.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_analyze_repository_use_case_dependency,
    get_repository_use_case_dependency,
)
from src.domain.entities.code_analysis import CodeAnalysis
from src.domain.entities.repository import Repository
from src.domain.exceptions import GitProviderError, RepositoryNotFoundError
from src.main import app


def _sample_repository() -> Repository:
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return Repository(
        id=1296269,
        name="Hello-World",
        full_name="octocat/Hello-World",
        owner="octocat",
        description="Sample repo",
        default_branch="main",
        is_private=False,
        html_url="https://github.com/octocat/Hello-World",
        clone_url="https://github.com/octocat/Hello-World.git",
        language="Python",
        stargazers_count=1,
        forks_count=0,
        created_at=now,
        updated_at=now,
    )


class _FakeUseCase:
    def __init__(self, repository: Repository | None = None, error: Exception | None = None) -> None:
        self._repository = repository
        self._error = error

    def execute(self, owner: str, name: str) -> Repository:
        if self._error is not None:
            raise self._error
        assert self._repository is not None
        return self._repository


class _FakeAnalysisUseCase:
    def __init__(self, analysis: CodeAnalysis | None = None, error: Exception | None = None) -> None:
        self._analysis = analysis
        self._error = error

    def execute(self, owner: str, name: str, ref: str | None = None) -> CodeAnalysis:
        if self._error is not None:
            raise self._error
        assert self._analysis is not None
        return self._analysis


def _sample_analysis() -> CodeAnalysis:
    return CodeAnalysis(
        language="Python",
        framework="FastAPI",
        dependencies=("fastapi", "uvicorn"),
        entry_point="main.py",
        has_dockerfile=False,
        manifest_file="requirements.txt",
    )


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_get_repository_success(client: TestClient) -> None:
    app.dependency_overrides[get_repository_use_case_dependency] = lambda: _FakeUseCase(
        repository=_sample_repository()
    )

    response = client.get("/repos/octocat/Hello-World")

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "octocat/Hello-World"
    assert body["owner"] == "octocat"


def test_get_repository_not_found(client: TestClient) -> None:
    app.dependency_overrides[get_repository_use_case_dependency] = lambda: _FakeUseCase(
        error=RepositoryNotFoundError("Repository 'octocat/missing' not found")
    )

    response = client.get("/repos/octocat/missing")

    assert response.status_code == 404
    assert response.json()["error_code"] == "REPOSITORY_NOT_FOUND"


def test_get_repository_upstream_failure(client: TestClient) -> None:
    app.dependency_overrides[get_repository_use_case_dependency] = lambda: _FakeUseCase(
        error=GitProviderError("GitHub rejected the request (status 401).")
    )

    response = client.get("/repos/octocat/Hello-World")

    assert response.status_code == 502
    assert response.json()["error_code"] == "GIT_PROVIDER_ERROR"


def test_analyze_repository_success(client: TestClient) -> None:
    app.dependency_overrides[get_analyze_repository_use_case_dependency] = lambda: _FakeAnalysisUseCase(
        analysis=_sample_analysis()
    )

    response = client.get("/repos/octocat/Hello-World/analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "Python"
    assert body["framework"] == "FastAPI"
    assert set(body["dependencies"]) == {"fastapi", "uvicorn"}
    assert body["entry_point"] == "main.py"
    assert body["has_dockerfile"] is False


def test_analyze_repository_not_found(client: TestClient) -> None:
    app.dependency_overrides[get_analyze_repository_use_case_dependency] = lambda: _FakeAnalysisUseCase(
        error=RepositoryNotFoundError("Repository 'octocat/missing' not found")
    )

    response = client.get("/repos/octocat/missing/analysis")

    assert response.status_code == 404
    assert response.json()["error_code"] == "REPOSITORY_NOT_FOUND"


def test_analyze_repository_accepts_ref_query_param(client: TestClient) -> None:
    captured: dict[str, str | None] = {}

    class _CapturingUseCase(_FakeAnalysisUseCase):
        def execute(self, owner: str, name: str, ref: str | None = None) -> CodeAnalysis:
            captured["ref"] = ref
            return super().execute(owner, name, ref)

    app.dependency_overrides[get_analyze_repository_use_case_dependency] = lambda: _CapturingUseCase(
        analysis=_sample_analysis()
    )

    response = client.get("/repos/octocat/Hello-World/analysis", params={"ref": "feature-branch"})

    assert response.status_code == 200
    assert captured["ref"] == "feature-branch"
