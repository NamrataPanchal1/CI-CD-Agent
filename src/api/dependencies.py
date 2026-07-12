"""
FastAPI dependency providers.

These thin functions are what routers actually `Depends()` on. They pull
from the `Container` composition root, keeping route handlers free of any
knowledge of how settings/loggers/adapters are constructed.
"""
from __future__ import annotations

from src.application.interfaces.git_provider import IGitProvider
from src.application.use_cases.analyze_repository import AnalyzeRepositoryUseCase
from src.application.use_cases.get_repository import GetRepositoryUseCase
from src.core.config import Settings
from src.core.di_container import get_container


def get_settings_dependency() -> Settings:
    """FastAPI dependency that yields the application `Settings`."""
    return get_container().settings


def get_git_provider_dependency() -> IGitProvider:
    """FastAPI dependency that yields the configured `IGitProvider`."""
    return get_container().get_git_provider()


def get_repository_use_case_dependency() -> GetRepositoryUseCase:
    """FastAPI dependency that yields a ready-to-use `GetRepositoryUseCase`."""
    return GetRepositoryUseCase(git_provider=get_container().get_git_provider())


def get_analyze_repository_use_case_dependency() -> AnalyzeRepositoryUseCase:
    """FastAPI dependency that yields a ready-to-use `AnalyzeRepositoryUseCase`."""
    return AnalyzeRepositoryUseCase(git_provider=get_container().get_git_provider())
