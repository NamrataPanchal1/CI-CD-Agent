"""
Repository domain entity.

This is a pure domain object: it has no knowledge of GitHub, HTTP, or any
other infrastructure concern. `infrastructure/github/github_adapter.py` is
responsible for translating GitHub's JSON response into this shape — if we
ever add GitLab or Bitbucket support, they would map into the exact same
entity, and nothing in `application/` or `api/` would need to change.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Repository:
    """An immutable snapshot of a source-code repository's metadata."""

    id: int
    name: str
    full_name: str
    owner: str
    description: str | None
    default_branch: str
    is_private: bool
    html_url: str
    clone_url: str
    language: str | None
    stargazers_count: int
    forks_count: int
    created_at: datetime
    updated_at: datetime
