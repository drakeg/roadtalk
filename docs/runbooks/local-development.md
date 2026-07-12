# Local Development Environment

- Sprint: 1
- Deliverable: S01-D07
- Issue: #25

## Cost boundary

This environment runs only on the developer's machine and creates no AWS resources. PostgreSQL/PostGIS and optional Redis are local containers. RDS and other managed AWS services are explicitly excluded from this deliverable.

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

`make setup` creates an ignored `.env` from `.env.example` only when it does not exist. The example password is local-only and must never be reused in a shared, field-test, or production environment.

## Services

| Service | Default host endpoint | Startup |
|---|---|---|
| PostgreSQL 17 + PostGIS 3.5 | `127.0.0.1:5432` | `make up` |
| Redis 8 | `127.0.0.1:6379` | `make up-redis` |

Both ports bind only to loopback. Redis is optional and excluded from the default Compose profile.

## Commands

| Command | Result |
|---|---|
| `make prerequisites` | Check Docker, daemon, and Compose. |
| `make setup` | Create local environment file if absent and validate Compose. |
| `make config` | Validate the resolved Compose model. |
| `make up` | Start and wait for PostgreSQL/PostGIS. |
| `make up-redis` | Start database and optional Redis. |
| `make wait` | Wait for database health with a bounded timeout. |
| `make verify-database` | Query PostgreSQL and PostGIS versions. |
| `make ps` | Display service health/status. |
| `make logs` | Follow recent logs. |
| `make database-shell` | Open psql. |
| `make redis-cli` | Open redis-cli. |
| `make down` | Stop containers without deleting data. |
| `make reset CONFIRM_RESET=yes` | Delete local containers and named volumes. |

## Data safety

- Named volumes persist across `make down`.
- `make reset` refuses to run without explicit confirmation.
- Local data is synthetic only.
- There is no production-data import path.
- `.env` is ignored; only `.env.example` is committed.

## Application integration

D03/D04 add the backend service, migrations, and tests. D02 documents physical-device and emulator API addressing. Until those deliverables land, this environment intentionally supplies only database and optional cache dependencies.

## Troubleshooting

### Port already in use

Change `POSTGRES_PORT` or `REDIS_PORT` in `.env`, run `make config`, and restart.

### Unhealthy database

Run `make ps` and `make logs`. If local data is disposable, use the explicitly confirmed reset and restart.

### Apple Silicon or ARM Linux

The selected images are multi-platform. Do not force an x86 platform unless a documented compatibility issue requires it.

## Validation

- Compose YAML and interpolation parse
- database binds to loopback
- Redis is optional behind a profile and binds to loopback
- no secret file is committed
- reset requires explicit confirmation
- shell scripts pass syntax checks
- live container validation is required on a Docker-capable developer or CI runner
