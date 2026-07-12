"""
Dependency Injection container.

Design decision:
    Routers and use cases must never instantiate infrastructure adapters
    (boto3 clients, GitHub clients, Bedrock clients, etc.) directly. Instead,
    they depend on abstract interfaces defined in `src/application/interfaces`,
    and this container is the single place responsible for wiring a concrete
    adapter to each interface.

    In Phase 1 there are no adapters yet, so the container only exposes
    settings/logging. From Phase 2 onward, methods like `get_git_provider()`
    will be added here, returning a concrete implementation of
    `IGitProvider`. This keeps FastAPI route handlers thin and keeps
    infrastructure swappable/mockable for tests.
"""
from __future__ import annotations

from src.application.interfaces.git_provider import IGitProvider
from src.core.config import Settings, get_settings
from src.core.logging import get_logger


class Container:
    """Application-wide composition root.

    A single `Container` instance is created at startup and exposed to
    FastAPI via `Depends`. Methods are intentionally simple factory
    functions rather than a full third-party DI framework, keeping the
    dependency graph easy to read and reason about.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._git_provider: IGitProvider | None = None

    @property
    def settings(self) -> Settings:
        return self._settings

    def get_logger(self, name: str):
        return get_logger(name)

    def get_git_provider(self) -> IGitProvider:
        """Return the configured `IGitProvider` implementation (GitHub today).

        Constructed lazily and cached for the lifetime of the container so
        the underlying HTTP connection pool is reused across requests.
        Swapping providers (e.g. adding GitLab) later means changing this
        one method — nothing in `application/` or `api/` needs to know.
        """
        if self._git_provider is None:
            # Local import avoids importing httpx/adapters when the
            # container is used without ever touching GitHub (e.g. in
            # Phase-1-only tests).
            from src.infrastructure.github.github_adapter import GitHubAdapter

            self._git_provider = GitHubAdapter(
                token=self._settings.github_token,
                base_url=self._settings.github_api_base_url,
                timeout_seconds=self._settings.github_request_timeout_seconds,
            )
        return self._git_provider


_container: Container | None = None


def get_container() -> Container:
    """Return the process-wide `Container` singleton."""
    global _container
    if _container is None:
        _container = Container()
    return _container
