# AI-CI-CD-Agent

An AI-powered CI/CD automation platform, built **incrementally, phase by
phase**. Each phase is fully working and independently runnable before the
next one begins.

**End-state capabilities (not all built yet):** detect GitHub repositories,
analyze source code, generate Dockerfiles with AI (Amazon Bedrock / Claude),
open pull requests, wait for human approval, build Docker images, run
security scans, execute tests, push to Amazon ECR, deploy, monitor for
failures, retry, and send email alerts.

## Tech Stack
- **Backend:** Python 3.12, FastAPI
- **Containerization:** Docker
- **Cloud:** AWS (Lambda, API Gateway, CodeBuild, CodePipeline, ECR, ECS,
  EventBridge, DynamoDB, SES, IAM, CloudWatch — introduced in later phases)
- **Infrastructure as Code:** AWS CDK (Python) — introduced in later phases
- **AI:** Amazon Bedrock (Claude) — introduced in later phases
- **Testing:** Pytest

## Architecture

Clean Architecture (ports & adapters):

```
src/
├── domain/          # Pure business entities & exceptions — zero third-party deps
├── application/     # Use cases + abstract interfaces (ports)
├── infrastructure/  # Concrete adapters (GitHub, AWS, Bedrock, Docker, DB)
├── api/              # FastAPI routers, request/response schemas, DI wiring
├── core/              # Config, logging, DI container
└── main.py            # App entrypoint
```

Outer layers depend on inner layers, never the reverse. This keeps business
logic testable without real AWS/GitHub credentials, and keeps every external
integration swappable behind an interface.

## Project Status

| Phase | Status |
|---|---|
| **1. Project Skeleton** | ✅ Complete |
| **2. GitHub repo detection** | ✅ Complete |
| **3. Source code analysis** | ✅ Complete |
| 4. AI Dockerfile generation (Bedrock) | ⏳ Not started |
| 5. Automated PR creation | ⏳ Not started |
| 6+. Approval, build, scan, test, ECR, deploy, monitor, retry, alert | ⏳ Not started |

---

## Phase 1 — Project Skeleton

**What it does:** A running FastAPI service with structured logging,
environment-driven configuration, and a `GET /health` endpoint — the
foundation every later phase builds on.

### Environment Variables

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `AI-CI-CD-Agent` | Application name, shown in `/health` |
| `APP_VERSION` | `0.1.0` | Application version |
| `APP_ENV` | `development` | One of `development`, `staging`, `production`, `test` |
| `API_HOST` | `0.0.0.0` | Host uvicorn binds to |
| `API_PORT` | `8000` | Port uvicorn binds to |
| `LOG_LEVEL` | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FORMAT` | `json` | `json` (production/CloudWatch-friendly) or `text` (local dev) |

### Run Locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Visit:
- `http://localhost:8000/health` — health check
- `http://localhost:8000/docs` — interactive Swagger UI

### Run with Docker

```bash
docker-compose up --build
curl http://localhost:8000/health
```

### Run Tests

```bash
pip install -r requirements.txt
pytest
```

### Design Decisions

See [`docs/phase-01-notes.md`](docs/phase-01-notes.md) for the full
reasoning behind Phase 1's structure and choices.

---

---

## Phase 2 — GitHub Repository Detection

**What it does:** Fetches metadata for a single, explicitly-named GitHub
repository via a Personal Access Token.

### New Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GITHUB_TOKEN` | *(empty)* | **Required** for `/repos/*` endpoints. A GitHub PAT with `repo` (or `public_repo`) scope. |
| `GITHUB_API_BASE_URL` | `https://api.github.com` | GitHub REST API base URL |
| `GITHUB_REQUEST_TIMEOUT_SECONDS` | `10.0` | HTTP timeout for GitHub calls |

### New Endpoint

```
GET /repos/{owner}/{name}
```

Example:
```bash
curl http://localhost:8000/repos/octocat/Hello-World
```

Response:
```json
{
  "id": 1296269,
  "name": "Hello-World",
  "full_name": "octocat/Hello-World",
  "owner": "octocat",
  "description": "This your first repo!",
  "default_branch": "main",
  "is_private": false,
  "html_url": "https://github.com/octocat/Hello-World",
  "clone_url": "https://github.com/octocat/Hello-World.git",
  "language": null,
  "stargazers_count": 80,
  "forks_count": 9,
  "created_at": "2011-01-26T19:01:12+00:00",
  "updated_at": "2024-05-01T10:00:00+00:00"
}
```

Error responses:
| Status | When |
|---|---|
| `404` | Repository doesn't exist or isn't accessible with the configured token |
| `502` | GitHub itself failed (bad/missing token, network error, rate limit) |
| `500` | `GITHUB_TOKEN` isn't configured at all |

### Design Decisions

See [`docs/phase-02-notes.md`](docs/phase-02-notes.md).

---

---

## Phase 3 — Source Code Analysis

**What it does:** Analyzes a repository's technology stack — detected
language, framework, dependency names, likely entry-point file, and whether
a Dockerfile already exists. Reads via the GitHub API only (no local clone).

### New Endpoint

```
GET /repos/{owner}/{name}/analysis
GET /repos/{owner}/{name}/analysis?ref=<branch|tag|sha>
```

Example:
```bash
curl http://localhost:8000/repos/octocat/Hello-World/analysis
```

Response:
```json
{
  "language": "Python",
  "framework": "FastAPI",
  "dependencies": ["fastapi", "uvicorn"],
  "entry_point": "main.py",
  "has_dockerfile": false,
  "manifest_file": "requirements.txt"
}
```

### Coverage

| Ecosystem | Manifest detected | Dependencies parsed | Framework inferred |
|---|---|---|---|
| Python | `requirements.txt`, `pyproject.toml`, `Pipfile` | ✅ | ✅ (FastAPI, Django, Flask) |
| Node.js / TypeScript | `package.json` | ✅ | ✅ (Next.js, NestJS, Express, Vue, React) |
| Go, Java, Ruby, PHP | ✅ (filename only) | ❌ (later phase) | ❌ (later phase) |

### Design Decisions

See [`docs/phase-03-notes.md`](docs/phase-03-notes.md).

---

## Contributing / Development Rules

1. No future-phase code is added until explicitly requested.
2. Clean Architecture layering is preserved — no shortcuts that couple
   `domain`/`application` to a specific SDK.
3. All configuration goes through `src/core/config.py` — no hardcoded values.
4. Every module logs through `src/core/logging.py` — no `print()`.
5. Every phase ships with tests and a short design-notes doc in `docs/`.
