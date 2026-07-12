# Backend

Sprint 1 owner: S01-D03, S01-D04, and S01-D05.

The backend is a Python/FastAPI modular-monolith control API.

## Current foundation

S01-D03 and S01-D04 provide:

- typed environment configuration
- privacy-safe JSON logging
- request correlation IDs
- RFC 9457-style problem responses
- liveness, readiness, and version endpoints
- extensible readiness-check registry
- automated foundation tests
- SQLAlchemy account, device, and session models
- Alembic migrations with PostGIS enablement
- database readiness checks

No authentication API, location, proximity, channel, or media behavior exists yet.

## Local setup

From the repository root:

```sh
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -e 'backend[dev]'
make up
make backend-migrate
make backend-migration-check
make backend-test
make backend-run
```

The API listens on `127.0.0.1:8000` by default.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health/live` | Process liveness. |
| `GET /health/ready` | Registered dependency readiness. |
| `GET /api/v1/system/version` | API version and environment. |
| `GET /docs` | Local OpenAPI UI when enabled. |

## Checks

```sh
make backend-format-check
make backend-lint
make backend-typecheck
make backend-test
```

## Scope boundary

D04 adds PostgreSQL/PostGIS models and migrations. D05 adds anonymous device/session authentication. Later domains remain unimplemented until their approved sprints.
