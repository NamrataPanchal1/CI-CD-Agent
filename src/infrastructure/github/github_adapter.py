"""
GitHub adapter.

Implements `IGitProvider` against GitHub's REST API using a Personal Access
Token (PAT). We use plain `httpx` rather than a full GitHub SDK (e.g.
PyGithub) to keep the dependency footprint small and the HTTP behaviour
fully transparent/testable via `respx`.

Auth note: GitHub's REST API accepts `Authorization: Bearer <token>` for
both classic and fine-grained PATs, so a single adapter works with either
token type without configuration changes.
"""
from __future__ import annotations

import base64
from datetime import datetime

import httpx

from src.application.interfaces.git_provider import IGitProvider
from src.core.logging import get_logger
from src.domain.entities.repository import Repository
from src.domain.exceptions import ConfigurationError, GitProviderError, RepositoryNotFoundError

logger = get_logger(__name__)

_GITHUB_API_VERSION = "2022-11-28"


class GitHubAdapter(IGitProvider):
    """`IGitProvider` implementation backed by the GitHub REST API."""

    def __init__(self, token: str, base_url: str = "https://api.github.com", timeout_seconds: float = 10.0) -> None:
        if not token:
            raise ConfigurationError(
                "GITHUB_TOKEN is required to use GitHubAdapter but was not provided."
            )

        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout_seconds,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": _GITHUB_API_VERSION,
                "User-Agent": "AI-CI-CD-Agent",
            },
        )

    def get_repository(self, owner: str, name: str) -> Repository:
        path = f"/repos/{owner}/{name}"

        try:
            response = self._client.get(path)
        except httpx.HTTPError as exc:
            logger.error(
                "Network error while contacting GitHub",
                extra={"extra_fields": {"event": "github_network_error", "owner": owner, "repo": name}},
            )
            raise GitProviderError(f"Network error contacting GitHub: {exc}") from exc

        if response.status_code == 404:
            raise RepositoryNotFoundError(f"Repository '{owner}/{name}' was not found or is not accessible.")

        if response.status_code in (401, 403):
            logger.error(
                "GitHub authentication/authorization failure",
                extra={
                    "extra_fields": {
                        "event": "github_auth_error",
                        "status_code": response.status_code,
                        "owner": owner,
                        "repo": name,
                    }
                },
            )
            raise GitProviderError(
                f"GitHub rejected the request (status {response.status_code}). "
                "Check that GITHUB_TOKEN is valid and has access to this repository."
            )

        if response.status_code >= 400:
            raise GitProviderError(f"Unexpected GitHub API error (status {response.status_code}): {response.text[:200]}")

        return self._to_entity(response.json())

    def get_repository_tree(self, owner: str, name: str, ref: str) -> list[str]:
        path = f"/repos/{owner}/{name}/git/trees/{ref}"

        try:
            response = self._client.get(path, params={"recursive": "1"})
        except httpx.HTTPError as exc:
            logger.error(
                "Network error while fetching repository tree",
                extra={"extra_fields": {"event": "github_network_error", "owner": owner, "repo": name}},
            )
            raise GitProviderError(f"Network error contacting GitHub: {exc}") from exc

        if response.status_code == 404:
            raise RepositoryNotFoundError(
                f"Repository '{owner}/{name}' or ref '{ref}' was not found or is not accessible."
            )
        if response.status_code in (401, 403):
            raise GitProviderError(
                f"GitHub rejected the request (status {response.status_code}). "
                "Check that GITHUB_TOKEN is valid and has access to this repository."
            )
        if response.status_code >= 400:
            raise GitProviderError(f"Unexpected GitHub API error (status {response.status_code}): {response.text[:200]}")

        data = response.json()

        if data.get("truncated"):
            logger.warning(
                "GitHub tree response was truncated; analysis may be incomplete for very large repositories",
                extra={"extra_fields": {"event": "github_tree_truncated", "owner": owner, "repo": name}},
            )

        return [item["path"] for item in data.get("tree", []) if item.get("type") == "blob"]

    def get_file_content(self, owner: str, name: str, path: str, ref: str) -> str | None:
        api_path = f"/repos/{owner}/{name}/contents/{path}"

        try:
            response = self._client.get(api_path, params={"ref": ref})
        except httpx.HTTPError as exc:
            logger.error(
                "Network error while fetching file content",
                extra={"extra_fields": {"event": "github_network_error", "owner": owner, "repo": name, "path": path}},
            )
            raise GitProviderError(f"Network error contacting GitHub: {exc}") from exc

        if response.status_code == 404:
            return None
        if response.status_code in (401, 403):
            raise GitProviderError(
                f"GitHub rejected the request (status {response.status_code}). "
                "Check that GITHUB_TOKEN is valid and has access to this repository."
            )
        if response.status_code >= 400:
            raise GitProviderError(f"Unexpected GitHub API error (status {response.status_code}): {response.text[:200]}")

        data = response.json()

        if data.get("encoding") != "base64" or "content" not in data:
            raise GitProviderError(f"Unexpected content encoding for '{path}' from GitHub.")

        try:
            return base64.b64decode(data["content"]).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise GitProviderError(f"Could not decode content for '{path}': {exc}") from exc

    def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        self._client.close()

    @staticmethod
    def _to_entity(data: dict) -> Repository:
        return Repository(
            id=data["id"],
            name=data["name"],
            full_name=data["full_name"],
            owner=data["owner"]["login"],
            description=data.get("description"),
            default_branch=data.get("default_branch", "main"),
            is_private=bool(data.get("private", False)),
            html_url=data["html_url"],
            clone_url=data["clone_url"],
            language=data.get("language"),
            stargazers_count=int(data.get("stargazers_count", 0)),
            forks_count=int(data.get("forks_count", 0)),
            created_at=_parse_github_datetime(data["created_at"]),
            updated_at=_parse_github_datetime(data["updated_at"]),
        )


def _parse_github_datetime(value: str) -> datetime:
    """Parse GitHub's ISO-8601 timestamps (e.g. '2024-01-01T00:00:00Z')."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
