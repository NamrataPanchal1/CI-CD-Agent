"""Unit tests for `GetRepositoryUseCase`, using a fake `IGitProvider`."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.application.interfaces.git_provider import IGitProvider
from src.application.use_cases.get_repository import GetRepositoryUseCase
from src.domain.entities.repository import Repository
from src.domain.exceptions import RepositoryNotFoundError


class FakeGitProvider(IGitProvider):
    """In-memory `IGitProvider` test double — no network, no mocking framework."""

    def __init__(self, repository: Repository | None = None) -> None:
        self._repository = repository

    def get_repository(self, owner: str, name: str) -> Repository:
        if self._repository is None:
            raise RepositoryNotFoundError(f"Repository '{owner}/{name}' not found")
        return self._repository

    def get_repository_tree(self, owner: str, name: str, ref: str) -> list[str]:
        return []

    def get_file_content(self, owner: str, name: str, path: str, ref: str) -> str | None:
        return None


def _sample_repository() -> Repository:
    now = datetime.now(tz=timezone.utc)
    return Repository(
        id=1,
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


def test_execute_returns_repository_on_success() -> None:
    fake_provider = FakeGitProvider(repository=_sample_repository())
    use_case = GetRepositoryUseCase(git_provider=fake_provider)

    result = use_case.execute(owner="octocat", name="Hello-World")

    assert result.full_name == "octocat/Hello-World"


def test_execute_propagates_not_found() -> None:
    fake_provider = FakeGitProvider(repository=None)
    use_case = GetRepositoryUseCase(git_provider=fake_provider)

    with pytest.raises(RepositoryNotFoundError):
        use_case.execute(owner="octocat", name="missing-repo")
