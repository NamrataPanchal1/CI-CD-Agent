"""Unit tests for `GitHubAdapter`, with all HTTP calls mocked via respx."""
from __future__ import annotations

import httpx
import pytest
import respx

from src.domain.exceptions import ConfigurationError, GitProviderError, RepositoryNotFoundError
from src.infrastructure.github.github_adapter import GitHubAdapter

BASE_URL = "https://api.github.com"


def _sample_github_repo_payload() -> dict:
    return {
        "id": 1296269,
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "owner": {"login": "octocat"},
        "description": "This your first repo!",
        "default_branch": "main",
        "private": False,
        "html_url": "https://github.com/octocat/Hello-World",
        "clone_url": "https://github.com/octocat/Hello-World.git",
        "language": "Python",
        "stargazers_count": 80,
        "forks_count": 9,
        "created_at": "2011-01-26T19:01:12Z",
        "updated_at": "2024-05-01T10:00:00Z",
    }


def test_adapter_requires_token() -> None:
    with pytest.raises(ConfigurationError):
        GitHubAdapter(token="", base_url=BASE_URL)


@respx.mock
def test_get_repository_success() -> None:
    respx.get(f"{BASE_URL}/repos/octocat/Hello-World").mock(
        return_value=httpx.Response(200, json=_sample_github_repo_payload())
    )

    adapter = GitHubAdapter(token="fake-token", base_url=BASE_URL)
    repository = adapter.get_repository("octocat", "Hello-World")

    assert repository.id == 1296269
    assert repository.full_name == "octocat/Hello-World"
    assert repository.owner == "octocat"
    assert repository.default_branch == "main"
    assert repository.is_private is False
    assert repository.language == "Python"
    assert repository.stargazers_count == 80


@respx.mock
def test_get_repository_not_found() -> None:
    respx.get(f"{BASE_URL}/repos/octocat/does-not-exist").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )

    adapter = GitHubAdapter(token="fake-token", base_url=BASE_URL)

    with pytest.raises(RepositoryNotFoundError):
        adapter.get_repository("octocat", "does-not-exist")


@respx.mock
def test_get_repository_auth_failure() -> None:
    respx.get(f"{BASE_URL}/repos/octocat/Hello-World").mock(
        return_value=httpx.Response(401, json={"message": "Bad credentials"})
    )

    adapter = GitHubAdapter(token="invalid-token", base_url=BASE_URL)

    with pytest.raises(GitProviderError):
        adapter.get_repository("octocat", "Hello-World")


@respx.mock
def test_get_repository_network_error() -> None:
    respx.get(f"{BASE_URL}/repos/octocat/Hello-World").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    adapter = GitHubAdapter(token="fake-token", base_url=BASE_URL)

    with pytest.raises(GitProviderError):
        adapter.get_repository("octocat", "Hello-World")


@respx.mock
def test_get_repository_tree_returns_blob_paths_only() -> None:
    respx.get(f"{BASE_URL}/repos/octocat/Hello-World/git/trees/main").mock(
        return_value=httpx.Response(
            200,
            json={
                "sha": "abc123",
                "truncated": False,
                "tree": [
                    {"path": "src", "type": "tree"},
                    {"path": "src/main.py", "type": "blob"},
                    {"path": "requirements.txt", "type": "blob"},
                ],
            },
        )
    )

    adapter = GitHubAdapter(token="fake-token", base_url=BASE_URL)
    paths = adapter.get_repository_tree("octocat", "Hello-World", ref="main")

    assert paths == ["src/main.py", "requirements.txt"]


@respx.mock
def test_get_repository_tree_not_found() -> None:
    respx.get(f"{BASE_URL}/repos/octocat/Hello-World/git/trees/does-not-exist").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )

    adapter = GitHubAdapter(token="fake-token", base_url=BASE_URL)

    with pytest.raises(RepositoryNotFoundError):
        adapter.get_repository_tree("octocat", "Hello-World", ref="does-not-exist")


@respx.mock
def test_get_file_content_decodes_base64() -> None:
    import base64

    encoded = base64.b64encode(b"fastapi==0.115.6\n").decode("ascii")
    respx.get(f"{BASE_URL}/repos/octocat/Hello-World/contents/requirements.txt").mock(
        return_value=httpx.Response(200, json={"encoding": "base64", "content": encoded})
    )

    adapter = GitHubAdapter(token="fake-token", base_url=BASE_URL)
    content = adapter.get_file_content("octocat", "Hello-World", "requirements.txt", ref="main")

    assert content == "fastapi==0.115.6\n"


@respx.mock
def test_get_file_content_returns_none_when_missing() -> None:
    respx.get(f"{BASE_URL}/repos/octocat/Hello-World/contents/missing.txt").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )

    adapter = GitHubAdapter(token="fake-token", base_url=BASE_URL)
    content = adapter.get_file_content("octocat", "Hello-World", "missing.txt", ref="main")

    assert content is None
