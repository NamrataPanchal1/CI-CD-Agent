# Phase 2 — GitHub Repository Detection: Design Notes

## Scope
- `GET /repos/{owner}/{name}` — fetch metadata for one explicitly-named
  GitHub repository.
- Authentication via a GitHub Personal Access Token (`GITHUB_TOKEN`).
- Listing all repos for a user/org is explicitly **out of scope** — only
  single-repo lookup, per your decision.

## Key Decisions

**1. `IGitProvider` interface, not a direct GitHub dependency.**
`application/interfaces/git_provider.py` defines the contract; nothing in
`application/` or `api/` imports `httpx` or knows GitHub exists. The concrete
`GitHubAdapter` lives entirely in `infrastructure/github/`. This means
Phase 3+ use cases (source analysis, PR creation) depend on `IGitProvider`,
and if we ever add GitLab/Bitbucket, only a new adapter is needed.

**2. Plain `httpx` instead of PyGithub.**
A full GitHub SDK pulls in more surface area than we need for metadata
lookups. `httpx` keeps the adapter's behavior fully explicit and easy to
unit-test with `respx` (HTTP-level mocking, no SDK internals to fight).
We can revisit this if later phases (PR creation, file commits) need
GitHub features that are painful to hand-roll.

**3. `Authorization: Bearer <token>` for the PAT.**
GitHub's REST API accepts `Bearer` for both classic and fine-grained PATs,
so the adapter works with either without configuration changes.

**4. Domain exceptions, not `HTTPException`, inside the adapter/use case.**
`RepositoryNotFoundError` and `GitProviderError` are domain-layer
exceptions. A new `src/api/exception_handlers.py` maps them to HTTP status
codes (404 and 502 respectively) in exactly one place. Route handlers stay
free of `try/except` boilerplate, and this mapping will keep growing
cleanly as later phases add exceptions (e.g. `BuildFailedError`,
`ScanFailedError`).

**5. `GITHUB_TOKEN` defaults to empty string, not a hard startup failure.**
The app still boots and `/health` still works without a token configured —
only `/repos/*` fails, with a clear `CONFIGURATION_ERROR` (500) message.
This matches "every phase independently runnable": you shouldn't need
GitHub credentials just to confirm the service is alive.

**6. Repository domain entity is a frozen dataclass, not a Pydantic model.**
Keeps `domain/` free of third-party imports (Pydantic is a
framework/infrastructure concern here, even though it's "just" a validation
library). `api/schemas/repository.py::RepositoryResponse` is the Pydantic
model, built from the entity via `.from_entity()` — the translation happens
at the boundary, not inside the domain.

**7. Testing strategy — three layers, no real network calls.**
- `test_github_adapter.py`: mocks HTTP via `respx`, verifies the adapter's
  translation of real-shaped GitHub JSON and its error handling (404, 401,
  network error, missing token).
- `test_get_repository_use_case.py`: uses a hand-written `FakeGitProvider`
  (no mocking framework needed — it's a 5-line class) to test orchestration
  logic in isolation.
- `test_repository_endpoint.py`: uses FastAPI's `dependency_overrides` to
  swap in a fake use case, verifying routing/status-code/schema behavior
  without touching GitHub or requiring `GITHUB_TOKEN` in CI.

## What's Deliberately NOT in Phase 2
- No repo listing (`GET /repos` for a user/org).
- No webhook/event handling.
- No source code analysis (that's Phase 3).
- No rate-limit handling/retry beyond surfacing GitHub's error as-is.

## How to Verify This Phase
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set GITHUB_TOKEN=<your PAT>

uvicorn src.main:app --reload
curl http://localhost:8000/repos/octocat/Hello-World

pytest -v   # 12 tests, all mocked — no GITHUB_TOKEN required to run them
```
