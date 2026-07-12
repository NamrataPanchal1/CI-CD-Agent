"""Use case: fetch metadata for a single, explicitly-named repository."""
from __future__ import annotations

from src.application.interfaces.git_provider import IGitProvider
from src.core.logging import get_logger
from src.domain.entities.repository import Repository

logger = get_logger(__name__)


class GetRepositoryUseCase:
    """Orchestrates retrieval of a single repository's metadata.

    Deliberately thin for Phase 2 — it exists so that future phases (e.g.
    "Phase 3: source code analysis") can depend on this use case rather than
    reaching into `IGitProvider` directly, and so cross-cutting concerns
    (logging, caching, future authorization checks) have one place to live.
    """

    def __init__(self, git_provider: IGitProvider) -> None:
        self._git_provider = git_provider

    def execute(self, owner: str, name: str) -> Repository:
        logger.info(
            "Fetching repository metadata",
            extra={"extra_fields": {"event": "get_repository_started", "owner": owner, "repo": name}},
        )
        repository = self._git_provider.get_repository(owner, name)
        logger.info(
            "Repository metadata fetched successfully",
            extra={
                "extra_fields": {
                    "event": "get_repository_succeeded",
                    "owner": owner,
                    "repo": name,
                    "repository_id": repository.id,
                }
            },
        )
        return repository
