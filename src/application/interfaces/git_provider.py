"""
Git provider interface (port).

Any concrete adapter (GitHub today; GitLab/Bitbucket possible later) must
implement this interface. Use cases depend only on this abstraction, never
on a concrete adapter or its SDK/HTTP client — that's what makes the
provider swappable and mockable in tests.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.repository import Repository


class IGitProvider(ABC):
    """Port for read access to a git hosting provider."""

    @abstractmethod
    def get_repository(self, owner: str, name: str) -> Repository:
        """Fetch metadata for a single repository.

        Args:
            owner: The repository owner (user or organization login).
            name: The repository name.

        Returns:
            A `Repository` domain entity.

        Raises:
            RepositoryNotFoundError: If no such repository exists or it is
                inaccessible with the configured credentials.
            GitProviderError: For any other upstream failure (auth, network,
                rate limiting, unexpected response).
        """
        raise NotImplementedError

    @abstractmethod
    def get_repository_tree(self, owner: str, name: str, ref: str) -> list[str]:
        """Return a flat list of file paths (blobs only) at the given ref.

        Args:
            owner: The repository owner.
            name: The repository name.
            ref: A branch, tag, or commit SHA to read the tree from.

        Returns:
            A list of file paths relative to the repository root. Directory
            entries are excluded — only actual files ("blobs").

        Raises:
            RepositoryNotFoundError: If the repository or ref doesn't exist.
            GitProviderError: For any other upstream failure.
        """
        raise NotImplementedError

    @abstractmethod
    def get_file_content(self, owner: str, name: str, path: str, ref: str) -> str | None:
        """Return the UTF-8 text content of a single file, or None if absent.

        Args:
            owner: The repository owner.
            name: The repository name.
            path: File path relative to the repository root.
            ref: A branch, tag, or commit SHA to read the file from.

        Returns:
            The file's decoded text content, or `None` if the file does not
            exist at that path/ref (this is a normal, expected outcome —
            callers use it to probe for optional manifest files).

        Raises:
            GitProviderError: For any upstream failure other than "not found".
        """
        raise NotImplementedError
