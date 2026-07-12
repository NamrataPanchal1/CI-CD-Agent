# Phase 1 — Project Skeleton: Design Notes

## Scope
- FastAPI application skeleton following Clean Architecture layering.
- `GET /health` endpoint.
- Environment-driven configuration (`pydantic-settings`).
- Structured (JSON) logging shared across the app.
- Minimal DI container as the composition root for future adapters.
- Dockerfile + docker-compose for containerized local runs.
- Unit tests for the health endpoint.

## Key Decisions

**1. Clean Architecture from day one, even though it looks "empty" now.**
`domain/`, `application/`, `infrastructure/`, and `api/` are all scaffolded now,
even though only `api/` and `core/` have real content in Phase 1. This avoids a
painful restructuring later — Phase 2 (GitHub integration) will add an
`IGitProvider` interface in `application/interfaces/` and a concrete
`GitHubAdapter` in `infrastructure/github/`, without touching anything built
in Phase 1.

**2. `pydantic-settings` over raw `os.environ`.**
Gives us type validation at startup (the app fails fast with a clear error if
`API_PORT` isn't an int, for example) instead of failing confusingly mid-request.
`Settings` is the single source of truth; nothing else reads environment
variables directly.

**3. JSON logging by default, switchable to text.**
Production/staging default to `LOG_FORMAT=json` because CloudWatch Logs
Insights and most log aggregators parse JSON natively, letting us later query
things like `event="pipeline_failed"` directly. Local development can set
`LOG_FORMAT=text` for readability.

**4. A hand-rolled DI container instead of a framework (e.g. `dependency-injector`).**
At this scale, a small `Container` class with explicit factory methods is
easier to read and debug than a DI framework's magic. It also keeps FastAPI's
own `Depends()` mechanism as the only "framework" in play at the API layer.
We may reconsider this if the dependency graph gets significantly more
complex in later phases.

**5. Non-root Docker user.**
The container runs as `appuser`, not root — a standard security hardening
step with no downside for this workload.

**6. `on_event("startup"/"shutdown")` instead of lifespan context manager.**
FastAPI's newer `lifespan` API is preferred going forward, but for a
single, dependency-free startup log line, `on_event` keeps Phase 1 minimal.
We'll likely switch to `lifespan` once we have real resources to acquire/
release (e.g. a boto3 session, a DB connection pool) in a later phase.

## What's Deliberately NOT in Phase 1
- No GitHub, AWS, Bedrock, or Docker-build code — those are Phase 2+.
- No persistence layer (DynamoDB) — added when pipeline state needs storing.
- No CDK infra — added once there's something real to provision.

## How to Verify This Phase
```bash
# Local
pip install -r requirements.txt
cp .env.example .env
uvicorn src.main:app --reload
curl http://localhost:8000/health

# Docker
docker-compose up --build
curl http://localhost:8000/health

# Tests
pytest
```
