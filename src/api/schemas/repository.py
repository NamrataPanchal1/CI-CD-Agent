"""Response schemas for repository endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.entities.repository import Repository


class RepositoryResponse(BaseModel):
    """Shape of a repository metadata response."""

    id: int
    name: str
    full_name: str = Field(..., examples=["octocat/Hello-World"])
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

    @classmethod
    def from_entity(cls, repository: Repository) -> "RepositoryResponse":
        return cls(
            id=repository.id,
            name=repository.name,
            full_name=repository.full_name,
            owner=repository.owner,
            description=repository.description,
            default_branch=repository.default_branch,
            is_private=repository.is_private,
            html_url=repository.html_url,
            clone_url=repository.clone_url,
            language=repository.language,
            stargazers_count=repository.stargazers_count,
            forks_count=repository.forks_count,
            created_at=repository.created_at,
            updated_at=repository.updated_at,
        )
