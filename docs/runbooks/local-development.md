# Local Development Environment

- Origin: Sprint 1 foundation, refreshed for post-Sprint-6 alpha readiness
- Local-only cost: $0

## Cost boundary

This environment runs only on the developer's machine and creates no AWS or LiveKit
resources. PostgreSQL/PostGIS and the FastAPI backend run as local containers. Redis
remains optional behind a Compose profile and is not required by the current product.

## Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose v2 plugin
- POSIX shell and Make

## First setup

```sh
make setup
make up
make verify-database
```

`make setup` creates an ignored `.env` from `.env.example` only when it does not
exist. `make up` builds the backend image, upgrades the database through Alembic,
starts PostgreSQL/PostGIS and the FastAPI backend, waits for health, and prints the
local API/docs URLs.

The backend image also downloads the pinned LiveKit browser client during the image
build and verifies its SHA-256 checksum. The running browser radio serves that asset
from RoadTalk itself, so using the radio does not depend on a third-party CDN request.

The example secrets are local-only and must never be reused in a shared, field-test,
or production environment.

## Services

| Service | Default host endpoint | Startup |
|---|---|---|
| RoadTalk FastAPI | `http://127.0.0.1:8000` | `make up` |
| PostgreSQL 17 + PostGIS 3.5 | `127.0.0.1:5432` | `make up` |
| Redis 8 | `127.0.0.1:6379` | `make up-redis` |

All published ports bind only to loopback. Redis is optional and excluded from the
default Compose profile.

## Changing the local API port

Set `BACKEND_PORT` in `.env` and restart the stack. No Compose-file edit is required.
For example:

```dotenv
BACKEND_PORT=18000
```

Then run:

```sh
make down
make up
```

The API will be available at `http://127.0.0.1:18000/api/v1` and Swagger UI at
`http://127.0.0.1:18000/docs`. `make local-url` prints the currently configured URLs.

The mobile Make targets derive `EXPO_PUBLIC_API_BASE_URL` from `BACKEND_PORT` by
default. For a physical phone, `localhost` refers to the phone itself, so set an
explicit LAN-reachable override in `.env`, for example:

```dotenv
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:18000/api/v1
```

That override changes only the mobile client endpoint. The Compose backend intentionally
remains loopback-bound for local safety; LAN/field-device exposure requires a separate,
explicit testing decision rather than silently broadening the bind address.

## Commands

| Command | Result |
|---|---|
| `make prerequisites` | Check Docker, daemon, and Compose. |
| `make setup` | Create `.env` if absent and validate Compose. |
| `make config` | Validate the resolved Compose model. |
| `make up` | Build/start API + PostgreSQL/PostGIS and wait for health. |
| `make up-redis` | Build/start API + database + optional Redis. |
| `make local-url` | Print configured API and docs URLs. |
| `make ps` | Display service health/status. |
| `make logs` | Follow recent service logs. |
| `make verify-database` | Query PostgreSQL and PostGIS versions. |
| `make database-shell` | Open psql. |
| `make redis-cli` | Open redis-cli when the optional profile is running. |
| `make down` | Stop containers without deleting data. |
| `make reset CONFIRM_RESET=yes` | Delete local containers and named volumes. |

## Host-process backend alternative

For debugger/reload workflows, stop the Compose backend first and run the API as a
host process instead:

```sh
docker compose --env-file .env stop backend
make backend-install
make backend-run
```

`make backend-run` uses the same `BACKEND_PORT` value as Compose. Do not run the
containerized backend and host backend simultaneously on the same host port.

## Data safety

- Named volumes persist across `make down`.
- `make reset` refuses to run without explicit confirmation.
- Local data is synthetic only.
- There is no production-data import path.
- `.env` is ignored; only `.env.example` is committed.

## Apple Silicon

The current PostGIS image is explicitly run as `linux/amd64`; Docker Desktop can
emulate it on Apple Silicon. This may be slower than a native-arm image but keeps the
local image version aligned with the validated stack.

## Validation

- Compose YAML and interpolation parse with the default port;
- Compose interpolation also resolves a non-default `BACKEND_PORT`;
- backend/database ports remain loopback-bound;
- backend runs migrations before serving and has a readiness healthcheck;
- browser voice code is checksum-pinned into the backend image and served locally;
- Redis remains optional behind a profile;
- no secret file is committed;
- reset requires explicit confirmation;
- no AWS or LiveKit resource/call is introduced.
