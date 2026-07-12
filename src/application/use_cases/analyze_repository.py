"""Use case: analyze a repository's technology stack.

Combines repository metadata, the file tree, and a detected manifest file's
contents into a `CodeAnalysis`. All actual interpretation logic (dependency
parsing, framework detection, entry-point guessing) lives in
`application/services/code_analyzer.py` — this use case is responsible for
orchestration and I/O sequencing only.
"""
from __future__ import annotations

from src.application.interfaces.git_provider import IGitProvider
from src.application.services import code_analyzer
from src.core.logging import get_logger
from src.domain.entities.code_analysis import CodeAnalysis

logger = get_logger(__name__)

_DOCKERFILE_FILENAME = "Dockerfile"


class AnalyzeRepositoryUseCase:
    """Orchestrates full source-code analysis for a single repository."""

    def __init__(self, git_provider: IGitProvider) -> None:
        self._git_provider = git_provider

    def execute(self, owner: str, name: str, ref: str | None = None) -> CodeAnalysis:
        logger.info(
            "Analyzing repository",
            extra={"extra_fields": {"event": "analyze_repository_started", "owner": owner, "repo": name}},
        )

        repository = self._git_provider.get_repository(owner, name)
        resolved_ref = ref or repository.default_branch

        tree_paths = self._git_provider.get_repository_tree(owner, name, resolved_ref)
        has_dockerfile = _DOCKERFILE_FILENAME in tree_paths

        language = repository.language
        manifest_file = code_analyzer.pick_manifest_file(language, tree_paths)

        dependencies: list[str] = []
        framework: str | None = None

        if manifest_file is not None:
            content = self._git_provider.get_file_content(owner, name, manifest_file, resolved_ref)
            if content is not None:
                dependencies, framework = code_analyzer.parse_manifest(manifest_file, content)

        entry_point = code_analyzer.detect_entry_point(language, tree_paths)

        analysis = CodeAnalysis(
            language=language,
            framework=framework,
            dependencies=tuple(dependencies),
            entry_point=entry_point,
            has_dockerfile=has_dockerfile,
            manifest_file=manifest_file,
        )

        logger.info(
            "Repository analysis complete",
            extra={
                "extra_fields": {
                    "event": "analyze_repository_succeeded",
                    "owner": owner,
                    "repo": name,
                    "language": language,
                    "framework": framework,
                    "has_dockerfile": has_dockerfile,
                    "dependency_count": len(dependencies),
                }
            },
        )

        return analysis
