"""Unit tests for `application/services/code_analyzer.py` — pure functions, no I/O."""
from __future__ import annotations

from src.application.services import code_analyzer


def test_pick_manifest_file_uses_language_hint() -> None:
    tree = ["README.md", "requirements.txt", "src/main.py"]
    assert code_analyzer.pick_manifest_file("Python", tree) == "requirements.txt"


def test_pick_manifest_file_falls_back_when_language_unknown() -> None:
    tree = ["README.md", "package.json"]
    assert code_analyzer.pick_manifest_file(None, tree) == "package.json"


def test_pick_manifest_file_returns_none_when_absent() -> None:
    tree = ["README.md", "src/main.py"]
    assert code_analyzer.pick_manifest_file("Python", tree) is None


def test_parse_requirements_txt_strips_versions_and_comments() -> None:
    content = "\n".join(
        [
            "# a comment",
            "fastapi==0.115.6",
            "uvicorn[standard]==0.34.0",
            "",
            "-r base.txt",
            "requests>=2.0",
        ]
    )
    assert code_analyzer.parse_requirements_txt(content) == ["fastapi", "uvicorn", "requests"]


def test_parse_pyproject_toml_pep621() -> None:
    content = """
[project]
name = "demo"
dependencies = ["fastapi>=0.100", "uvicorn[standard]"]
"""
    assert code_analyzer.parse_pyproject_toml(content) == ["fastapi", "uvicorn"]


def test_parse_pyproject_toml_poetry_fallback() -> None:
    content = """
[tool.poetry.dependencies]
python = "^3.12"
flask = "^3.0"
"""
    assert code_analyzer.parse_pyproject_toml(content) == ["flask"]


def test_parse_package_json_merges_dev_and_prod_deps() -> None:
    content = '{"dependencies": {"express": "^4.0.0"}, "devDependencies": {"jest": "^29.0.0"}}'
    deps = code_analyzer.parse_package_json(content)
    assert set(deps) == {"express", "jest"}


def test_detect_python_framework_fastapi() -> None:
    assert code_analyzer.detect_python_framework(["fastapi", "uvicorn"]) == "FastAPI"


def test_detect_python_framework_none_when_unrecognized() -> None:
    assert code_analyzer.detect_python_framework(["requests", "boto3"]) is None


def test_detect_node_framework_prioritizes_next_over_react() -> None:
    assert code_analyzer.detect_node_framework(["react", "next"]) == "Next.js"


def test_detect_entry_point_python() -> None:
    tree = ["src/app.py", "requirements.txt"]
    assert code_analyzer.detect_entry_point("Python", tree) == "app.py"


def test_detect_entry_point_returns_none_when_no_candidates_match() -> None:
    tree = ["src/weird_name.py"]
    assert code_analyzer.detect_entry_point("Python", tree) is None


def test_parse_manifest_dispatches_by_filename() -> None:
    deps, framework = code_analyzer.parse_manifest("requirements.txt", "flask==3.0\n")
    assert deps == ["flask"]
    assert framework == "Flask"
