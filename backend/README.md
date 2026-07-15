# Backend

Sprint 2 active owner: S02-D04 Profile and identity API.

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

Profile persistence supports an incomplete identity without inventing a callsign or avatar. S02-D04 adds owner-scoped profile reads and conditional callsign updates using the shared policy. Avatar mutation is validated against the bundled catalog, and optional anonymous recovery remains PII-free.

S03-D02 adds persistence only for append-only foreground-location consent decisions
and one expiring PostGIS geography point per account. The current row is owned by the
account and source device, contains quality/sequence/expiry metadata, and cascades on
account or source-device deletion. No location API, mobile permission, background
collection, history table, cache, map, or nearby response is implemented in D02.

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
| `GET /api/v1/callsigns/availability?callsign=...` | Authenticated, rate-limited callsign check. |
| `POST /api/v1/me/recovery-key` | Create or rotate an authenticated account recovery key. |
| `POST /api/v1/sessions/recover` | Transfer an anonymous account and establish a replacement session. |
| `GET /api/v1/me/profile` | Read the authenticated account's private setup state and minimal public identity. |
| `PATCH /api/v1/me/profile` | Conditionally update the authenticated account's callsign. |

## Checks

```sh
make backend-format-check
make backend-lint
make backend-typecheck
make backend-test
ROADTALK_RUN_DATABASE_TESTS=1 make backend-test  # migrated disposable database only
```

## Scope boundary

S02-D04 exposes only the authenticated account at `/api/v1/me/profile`; callers cannot
select another account. Version `0` represents an uninitialized profile, and every
write must supply the current version. Stale writes, unknown fields, callsign
collisions, and cooldown violations fail closed. The reusable public identity DTO
contains only display callsign and bundled-avatar identifier. Avatar changes remain
read-only until S02-D05 supplies catalog validation. No AWS resources, Terraform
changes, or managed services are added.


## Anonymous recovery

S02-D07 adds optional recovery without email, SMS, passwords, or hosted identity.
A recovery key contains a non-secret random lookup selector and at least 256 bits of
secret entropy. The server stores the selector plus only a salted, versioned scrypt
hash of the complete key, protected by a separate application pepper.

Creating or rotating a key returns plaintext once. Successful recovery atomically
rotates the key, revokes every existing account session, transfers an eligible fresh
installation, and creates a replacement session. Invalid, unknown, and replayed keys
share the same failure response. Abuse controls are bounded and process-local for the
current single-worker field-test design; direct peer address, installation, selector,
account, and device dimensions are checked without logging their values.

Recovery material must never enter logs, analytics, URLs, ordinary storage, or support
workflows. A multi-worker deployment requires a separately approved shared rate-limit
design. This implementation adds no AWS resources or managed cache.
