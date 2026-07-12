"""
CodeAnalysis domain entity.

Pure domain object describing what we were able to infer about a
repository's technology stack — used as the input to later phases
(AI Dockerfile generation). No GitHub/HTTP knowledge lives here; that
belongs to the use case and adapters that populate it.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CodeAnalysis:
    """Inferred technology profile of a repository at a given ref."""

    language: str | None
    framework: str | None
    dependencies: tuple[str, ...]
    entry_point: str | None
    has_dockerfile: bool
    manifest_file: str | None
