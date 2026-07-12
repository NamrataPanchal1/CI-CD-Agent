"""Response schemas for the code-analysis endpoint."""
from __future__ import annotations

from pydantic import BaseModel, Field

from src.domain.entities.code_analysis import CodeAnalysis


class CodeAnalysisResponse(BaseModel):
    """Shape of the `GET /repos/{owner}/{name}/analysis` response."""

    language: str | None = Field(..., examples=["Python"])
    framework: str | None = Field(..., examples=["FastAPI"])
    dependencies: list[str]
    entry_point: str | None = Field(..., examples=["src/main.py"])
    has_dockerfile: bool
    manifest_file: str | None = Field(..., examples=["requirements.txt"])

    @classmethod
    def from_entity(cls, analysis: CodeAnalysis) -> "CodeAnalysisResponse":
        return cls(
            language=analysis.language,
            framework=analysis.framework,
            dependencies=list(analysis.dependencies),
            entry_point=analysis.entry_point,
            has_dockerfile=analysis.has_dockerfile,
            manifest_file=analysis.manifest_file,
        )
