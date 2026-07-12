"""
Code analysis heuristics.

Design decision:
    All functions here are pure (no I/O, no GitHub/HTTP knowledge) — they
    take data the use case has already fetched and interpret it. This keeps
    the actual detection logic trivially unit-testable and independently
    reusable (e.g. Phase 4's Dockerfile generation can call these directly
    without going through the use case).

Scope note (Phase 3):
    Full manifest parsing + framework detection is implemented for Python
    and Node.js/TypeScript, the two ecosystems most directly relevant to
    this project's own stack. Java, Go, Ruby, and PHP get manifest-file
    *detection* (so `has_dockerfile`/`manifest_file` results are still
    accurate) but not dependency parsing or framework inference yet — that
    can be added in a later phase without changing this module's shape.
"""
from __future__ import annotations

import json
import re
import tomllib

# Root-level manifest filenames to look for, keyed by GitHub's reported
# primary language, in priority order.
MANIFEST_CANDIDATES: dict[str, tuple[str, ...]] = {
    "Python": ("requirements.txt", "pyproject.toml", "Pipfile"),
    "JavaScript": ("package.json",),
    "TypeScript": ("package.json",),
    "Go": ("go.mod",),
    "Java": ("pom.xml", "build.gradle"),
    "Ruby": ("Gemfile",),
    "PHP": ("composer.json",),
}

# Dependency-name markers used to infer a framework, checked in order.
_PY_FRAMEWORK_MARKERS: tuple[tuple[str, str], ...] = (
    ("fastapi", "FastAPI"),
    ("django", "Django"),
    ("flask", "Flask"),
)

_NODE_FRAMEWORK_MARKERS: tuple[tuple[str, str], ...] = (
    ("next", "Next.js"),
    ("@nestjs/core", "NestJS"),
    ("express", "Express"),
    ("vue", "Vue.js"),
    ("react", "React"),
)

_PY_ENTRY_POINT_CANDIDATES = ("manage.py", "main.py", "app.py", "asgi.py", "wsgi.py")
_NODE_ENTRY_POINT_CANDIDATES = ("index.js", "server.js", "app.js", "index.ts", "server.ts")

_DEPENDENCY_NAME_SPLIT_PATTERN = re.compile(r"[=<>!~\[; ]")


def pick_manifest_file(language: str | None, tree_paths: list[str]) -> str | None:
    """Return the first known root-level manifest filename present in the tree.

    If `language` maps to known manifest filenames, only those are checked
    (in priority order). Otherwise every known manifest filename is checked,
    so an unrecognized/missing `language` still yields a best-effort result.
    """
    if language and language in MANIFEST_CANDIDATES:
        candidates: tuple[str, ...] = MANIFEST_CANDIDATES[language]
    else:
        candidates = tuple(name for names in MANIFEST_CANDIDATES.values() for name in names)

    tree_set = set(tree_paths)
    for candidate in candidates:
        if candidate in tree_set:
            return candidate
    return None


def parse_requirements_txt(content: str) -> list[str]:
    """Extract bare dependency names from a `requirements.txt` file."""
    dependencies: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = _DEPENDENCY_NAME_SPLIT_PATTERN.split(line, maxsplit=1)[0].strip()
        if name:
            dependencies.append(name)
    return dependencies


def parse_pyproject_toml(content: str) -> list[str]:
    """Extract dependency names from PEP 621 or Poetry-style `pyproject.toml`."""
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        return []

    pep621_deps = data.get("project", {}).get("dependencies", [])
    names = [
        name
        for dep in pep621_deps
        if (name := _DEPENDENCY_NAME_SPLIT_PATTERN.split(dep, maxsplit=1)[0].strip())
    ]

    if names:
        return names

    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    return [name for name in poetry_deps if name.lower() != "python"]


def parse_package_json(content: str) -> list[str]:
    """Extract dependency names (prod + dev) from `package.json`."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    dependencies: dict[str, str] = dict(data.get("dependencies", {}))
    dependencies.update(data.get("devDependencies", {}))
    return list(dependencies.keys())


def detect_python_framework(dependencies: list[str]) -> str | None:
    lowered = {dep.lower() for dep in dependencies}
    for marker, framework in _PY_FRAMEWORK_MARKERS:
        if marker in lowered:
            return framework
    return None


def detect_node_framework(dependencies: list[str]) -> str | None:
    lowered = {dep.lower() for dep in dependencies}
    for marker, framework in _NODE_FRAMEWORK_MARKERS:
        if marker in lowered:
            return framework
    return None


def detect_entry_point(language: str | None, tree_paths: list[str]) -> str | None:
    """Best-effort guess at the application's entry-point file.

    Matches by basename anywhere in the tree (not just at the repository
    root), since entry points commonly live under `src/`, `app/`, etc.
    """
    if language == "Python":
        candidates = _PY_ENTRY_POINT_CANDIDATES
    elif language in ("JavaScript", "TypeScript"):
        candidates = _NODE_ENTRY_POINT_CANDIDATES
    else:
        return None

    basenames = {path.rsplit("/", 1)[-1] for path in tree_paths}
    for candidate in candidates:
        if candidate in basenames:
            return candidate
    return None


def parse_manifest(manifest_file: str, content: str) -> tuple[list[str], str | None]:
    """Parse a manifest file's content into (dependencies, framework)."""
    if manifest_file == "requirements.txt":
        deps = parse_requirements_txt(content)
        return deps, detect_python_framework(deps)
    if manifest_file == "pyproject.toml":
        deps = parse_pyproject_toml(content)
        return deps, detect_python_framework(deps)
    if manifest_file == "package.json":
        deps = parse_package_json(content)
        return deps, detect_node_framework(deps)
    return [], None
