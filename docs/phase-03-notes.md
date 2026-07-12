# Phase 3 — Source Code Analysis: Design Notes

## Scope
- `GET /repos/{owner}/{name}/analysis?ref=<optional>` — analyze a
  repository's technology stack: language, framework, dependencies, entry
  point, and whether a Dockerfile already exists.
- No local `git clone` — reads via the GitHub API only (Git Trees API +
  Contents API), reusing the same `IGitProvider` port from Phase 2.

## Key Decisions

**1. GitHub API over local clone.**
You asked me to recommend an approach: I chose the GitHub API (Trees API
for the file listing, Contents API for specific manifest files) over
`git clone`. It fits directly into the existing `IGitProvider` port with no
new dependency, no subprocess/temp-directory lifecycle to manage, and no
disk space concerns for arbitrary repo sizes. The tradeoff is GitHub API
rate limits and a `truncated` flag on very large trees (>100k entries) —
acceptable for MVP; logged as a warning if it happens.

**2. `IGitProvider` gained two new methods, not a new interface.**
`get_repository_tree()` and `get_file_content()` were added to the existing
port rather than creating `ISourceReader` or similar. They're still
fundamentally "read from the git host" operations, and splitting them out
would have added indirection without a clear benefit at this stage. Revisit
if a future provider (e.g. GitLab) needs meaningfully different semantics.

**3. Detection logic is pure and separate from orchestration.**
`application/services/code_analyzer.py` contains only pure functions —
manifest selection, dependency parsing, framework inference, entry-point
guessing — with zero I/O. `AnalyzeRepositoryUseCase` handles fetching and
sequencing. This split means:
- The detection heuristics are trivially unit-tested (13 tests, no mocking).
- Phase 4 (AI Dockerfile generation) can reuse these functions directly.

**4. Scope limited to Python and Node.js/TypeScript for real parsing.**
Manifest-file *detection* covers Go, Java, Ruby, and PHP too (so
`manifest_file` and `has_dockerfile` are accurate for those repos), but
dependency parsing and framework inference are Python/Node-only for now.
This is an honest scope boundary, not a hidden gap — expanding it later
means adding new `parse_*`/`detect_*_framework` functions to
`code_analyzer.py`, with no changes to the use case or API layer.

**5. Entry-point detection matches by basename, not full path.**
A file like `src/main.py` still gets detected as entry point `main.py`,
because entry points commonly live under `src/`, `app/`, etc. This was a
real bug caught by the test suite during development (initial version only
matched root-level files) — fixed before this phase was considered done.

**6. `ref` defaults to the repository's default branch.**
The endpoint accepts an optional `?ref=` query param (branch/tag/SHA) but
falls back to whatever `GET /repos/{owner}/{name}` reports as
`default_branch`, so the common case ("just analyze the repo") needs no
extra input.

**7. Framework/language values stay as free-form strings, not enums.**
An enum would need updating every time we recognize a new framework.
Strings keep the domain entity open for extension; API consumers get a
stable JSON shape either way.

## What's Deliberately NOT in Phase 3
- No AI involvement yet — this is deterministic, rule-based analysis only.
  Phase 4 is where Bedrock/Claude comes in, consuming this phase's output.
- No dependency *version* extraction (see note below) — only names, since
  that's what's needed for AI Dockerfile generation prompts.
- No support for monorepos with multiple manifests (first match wins).

## How to Verify This Phase
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set GITHUB_TOKEN=<your PAT>

uvicorn src.main:app --reload
curl http://localhost:8000/repos/octocat/Hello-World/analysis

pytest -v   # 36 tests, all mocked — no GITHUB_TOKEN required to run them
```
