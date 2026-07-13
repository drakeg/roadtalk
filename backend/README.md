# Backend

Sprint 2 active owner: S02-D02 Profile persistence.

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
- SQLAlchemy account, device, session, and optional one-to-one profile models
- Alembic migrations with PostGIS enablement
- database readiness checks
- anonymous account/device registration
- short-lived device-bound access tokens
- hashed rotating refresh credentials, logout, device revocation, and replay-family revocation

Profile persistence now supports an incomplete identity without inventing a callsign or avatar for existing accounts. Profile APIs, callsign policy, avatar behavior, location, proximity, channels, media, and account recovery are not implemented by S02-D02.

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
| `POST /api/v1/auth/anonymous` | Register an anonymous account and device session. |
| `POST /api/v1/auth/refresh` | Rotate a refresh credential and issue a new token pair. |
| `GET /api/v1/auth/session` | Validate the current access token/session. |
| `POST /api/v1/auth/logout` | Revoke the current session. |
| `DELETE /api/v1/auth/devices/{device_id}` | Revoke all active sessions for an owned device. |

## Checks

```sh
make backend-format-check
make backend-lint
make backend-typecheck
make backend-test
ROADTALK_RUN_DATABASE_TESTS=1 make backend-test  # migrated disposable database only
```

## Scope boundary

S02-D02 adds only the nullable profile persistence boundary. It collects no callsign or avatar until a later explicit user action. The database remains local and containerized; this deliverable provisions no AWS resources or managed database. Later domains remain unimplemented until their approved deliverables.
