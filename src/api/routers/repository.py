"""Repository endpoints.

Phase 2 scope: fetch metadata for a single, explicitly-named repository
(`owner/name`). Listing all repos for a user/org is deliberately out of
scope for this phase.

Phase 3 scope: analyze that repository's technology stack (language,
framework, dependencies, entry point, existing Dockerfile).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import (
    get_analyze_repository_use_case_dependency,
    get_repository_use_case_dependency,
)
from src.api.schemas.code_analysis import CodeAnalysisResponse
from src.api.schemas.repository import RepositoryResponse
from src.application.use_cases.analyze_repository import AnalyzeRepositoryUseCase
from src.application.use_cases.get_repository import GetRepositoryUseCase
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/repos", tags=["repositories"])


@router.get(
    "/{owner}/{name}",
    response_model=RepositoryResponse,
    summary="Fetch metadata for a single GitHub repository",
)
def get_repository(
    owner: str,
    name: str,
    use_case: GetRepositoryUseCase = Depends(get_repository_use_case_dependency),
) -> RepositoryResponse:
    """Fetch metadata for the repository identified by `owner/name`.

    Raises:
        404: if the repository does not exist or is inaccessible with the
            configured `GITHUB_TOKEN`.
        502: if GitHub itself fails (auth, network, rate limiting, etc.).
    """
    repository = use_case.execute(owner=owner, name=name)
    return RepositoryResponse.from_entity(repository)


@router.get(
    "/{owner}/{name}/analysis",
    response_model=CodeAnalysisResponse,
    summary="Analyze a repository's technology stack",
)
def analyze_repository(
    owner: str,
    name: str,
    ref: str | None = Query(
        default=None,
        description="Branch, tag, or commit SHA to analyze. Defaults to the repository's default branch.",
    ),
    use_case: AnalyzeRepositoryUseCase = Depends(get_analyze_repository_use_case_dependency),
) -> CodeAnalysisResponse:
    """Analyze `owner/name` and return its detected language, framework,
    dependencies, entry point, and whether a Dockerfile already exists.

    Raises:
        404: if the repository or `ref` does not exist.
        502: if GitHub itself fails (auth, network, rate limiting, etc.).
    """
    analysis = use_case.execute(owner=owner, name=name, ref=ref)
    return CodeAnalysisResponse.from_entity(analysis)
