"""Unit tests for `AnalyzeRepositoryUseCase`, using a fake `IGitProvider`."""
from __future__ import annotations

from datetime import datetime, timezone

from src.application.interfaces.git_provider import IGitProvider
from src.application.use_cases.analyze_repository import AnalyzeRepositoryUseCase
from src.domain.entities.repository import Repository


class FakeAnalysisGitProvider(IGitProvider):
    """In-memory `IGitProvider` test double with configurable tree/content."""

    def __init__(
        self,
        repository: Repository,
        tree: list[str],
        file_contents: dict[str, str] | None = None,
    ) -> None:
        self._repository = repository
        self._tree = tree
        self._file_contents = file_contents or {}

    def get_repository(self, owner: str, name: str) -> Repository:
        return self._repository

    def get_repository_tree(self, owner: str, name: str, ref: str) -> list[str]:
        return self._tree

    def get_file_content(self, owner: str, name: str, path: str, ref: str) -> str | None:
        return self._file_contents.get(path)


def _sample_repository(language: str | None) -> Repository:
    now = datetime.now(tz=timezone.utc)
    return Repository(
        id=1,
        name="demo",
        full_name="octocat/demo",
        owner="octocat",
        description=None,
        default_branch="main",
        is_private=False,
        html_url="https://github.com/octocat/demo",
        clone_url="https://github.com/octocat/demo.git",
        language=language,
        stargazers_count=0,
        forks_count=0,
        created_at=now,
        updated_at=now,
    )


def test_analyze_python_fastapi_repository() -> None:
    provider = FakeAnalysisGitProvider(
        repository=_sample_repository("Python"),
        tree=["requirements.txt", "src/main.py", "README.md"],
        file_contents={"requirements.txt": "fastapi==0.115.6\nuvicorn[standard]==0.34.0\n"},
    )
    use_case = AnalyzeRepositoryUseCase(git_provider=provider)

    result = use_case.execute(owner="octocat", name="demo")

    assert result.language == "Python"
    assert result.framework == "FastAPI"
    assert set(result.dependencies) == {"fastapi", "uvicorn"}
    assert result.entry_point == "main.py"
    assert result.manifest_file == "requirements.txt"
    assert result.has_dockerfile is False


def test_analyze_node_express_repository_with_dockerfile() -> None:
    provider = FakeAnalysisGitProvider(
        repository=_sample_repository("JavaScript"),
        tree=["package.json", "index.js", "Dockerfile"],
        file_contents={"package.json": '{"dependencies": {"express": "^4.0.0"}}'},
    )
    use_case = AnalyzeRepositoryUseCase(git_provider=provider)

    result = use_case.execute(owner="octocat", name="demo")

    assert result.language == "JavaScript"
    assert result.framework == "Express"
    assert result.dependencies == ("express",)
    assert result.entry_point == "index.js"
    assert result.has_dockerfile is True


def test_analyze_repository_with_no_recognized_manifest() -> None:
    provider = FakeAnalysisGitProvider(
        repository=_sample_repository("Rust"),
        tree=["Cargo.toml", "src/main.rs"],
    )
    use_case = AnalyzeRepositoryUseCase(git_provider=provider)

    result = use_case.execute(owner="octocat", name="demo")

    assert result.language == "Rust"
    assert result.framework is None
    assert result.dependencies == ()
    assert result.manifest_file is None
    assert result.entry_point is None


def test_analyze_repository_uses_explicit_ref_over_default_branch() -> None:
    captured_refs: list[str] = []

    class RefCapturingProvider(FakeAnalysisGitProvider):
        def get_repository_tree(self, owner: str, name: str, ref: str) -> list[str]:
            captured_refs.append(ref)
            return super().get_repository_tree(owner, name, ref)

    provider = RefCapturingProvider(repository=_sample_repository("Python"), tree=[])
    use_case = AnalyzeRepositoryUseCase(git_provider=provider)

    use_case.execute(owner="octocat", name="demo", ref="feature-branch")

    assert captured_refs == ["feature-branch"]
