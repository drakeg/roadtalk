# Local Development Environment

- Origin: Sprint 1 foundation, refreshed for post-Sprint-6 alpha readiness
- Local-only cost: $0

## Cost boundary

This environment runs only on the developer's machine and creates no AWS or LiveKit
Cloud resources. PostgreSQL/PostGIS, self-hosted LiveKit, and the FastAPI backend run
as local containers. Redis remains optional behind a Compose profile.

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
starts PostgreSQL/PostGIS, self-hosted LiveKit, and the FastAPI backend, waits for
health, and prints the local URLs. Plain `docker compose up --build` starts the same
voice-ready stack in the foreground.

The RoadTalk web/API port binds to all local interfaces by default so ordinary home-LAN
testing does not require a second Compose file, a certificate, or a special Make target.
PostgreSQL and Redis remain loopback-only. Set `BACKEND_BIND_ADDRESS=127.0.0.1` in
`.env` if you want to restrict the web/API port to the Docker host again.

The backend image also downloads the pinned LiveKit browser client during the image
build and verifies its SHA-256 checksum. The running browser radio serves that asset
from RoadTalk itself, so using the radio does not depend on a third-party CDN request.

The example secrets are local-only and must never be reused in a shared, field-test,
or production environment.

The browser radio stores a non-sensitive monotonic location sequence in browser local
storage so replay protection continues to work after a page reload or reconnect. This
value contains no coordinates, call sign, token, or other location content. Clearing
site data safely resets it; the next value is seeded from the current time.

## Services

| Service | Default host endpoint | Startup |
|---|---|---|
| RoadTalk FastAPI | `http://127.0.0.1:8000` or `http://<host-LAN-IP>:8000` | `make up` or `docker compose up --build` |
| PostgreSQL 17 + PostGIS 3.5 | `127.0.0.1:5432` | `make up` |
| LiveKit signaling (local host) | `ws://127.0.0.1:7880` | `make up` |
| Redis 8 | `127.0.0.1:6379` | `make up-redis` |

The RoadTalk web/API port is LAN-reachable by default for simple testing. Database and
Redis ports remain loopback-only. LiveKit's WebRTC TCP/UDP media ports are published so
browsers and devices can establish audio when the secure LAN mode is used. Redis is
optional and excluded from the default Compose profile.

## Simple testing from another device on your home network

For ordinary UI, account, API, and workflow testing, start the normal stack:

```sh
docker compose up -d --build
```

Then browse from another trusted device on the same LAN to the Docker host's private
address, for example:

```text
http://192.168.1.100:8000/
```

No custom certificate or LAN-specific Compose command is required for this basic test
path. Your host firewall must allow inbound TCP traffic to the configured `BACKEND_PORT`
(default `8000`) from the trusted home subnet.

Browsers generally require a secure context for microphone and precise-location APIs.
Therefore plain HTTP on a private IP is suitable for ordinary application testing but
may block RoadTalk features that request microphone or browser geolocation permission.

Do not configure router port forwarding, public DNS, or internet exposure. This stack
uses development-only credentials and is intended only for a private, trusted network.

## Optional secure LAN testing for microphone/location

Use the HTTPS LAN mode only when you specifically need browser microphone, geolocation,
or secure LiveKit signaling behavior from another device:

```sh
make up-lan ROADTALK_LAN_HOST=192.168.1.100
make lan-ca ROADTALK_LAN_HOST=192.168.1.100
```

The LAN workflow adds a Caddy HTTPS gateway at
`https://192.168.1.100:8443/` and routes both the RoadTalk API and LiveKit signaling
through it. Caddy's local certificate authority is exported to
`.local/roadtalk-local-ca.crt`; trust that CA on the test device when you need the
browser to treat the private-IP HTTPS origin as secure.

Your host firewall must permit the following inbound traffic from the trusted home
subnet for full secure voice testing:

| Protocol | Port | Purpose |
|---|---:|---|
| TCP | 8443 | RoadTalk HTTPS and LiveKit secure signaling |
| TCP | 7881 | LiveKit WebRTC fallback |
| UDP | 7882 | LiveKit WebRTC media |

Stop the secure LAN overlay when testing is complete:

```sh
make down-lan ROADTALK_LAN_HOST=192.168.1.100
```

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

The API will be available at `http://127.0.0.1:18000/api/v1` and also at
`http://<host-LAN-IP>:18000/api/v1`; Swagger UI is available at the corresponding
`/docs` path. `make local-url` prints the host-local URLs.

To restrict the application to the Docker host only, set:

```dotenv
BACKEND_BIND_ADDRESS=127.0.0.1
```

The mobile Make targets derive `EXPO_PUBLIC_API_BASE_URL` from `BACKEND_PORT` by
default. For a physical phone, `localhost` refers to the phone itself, so set an
explicit LAN-reachable override in `.env`, for example:

```dotenv
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:18000/api/v1
```

## Commands

| Command | Result |
|---|---|
| `make prerequisites` | Check Docker, daemon, and Compose. |
| `make setup` | Create `.env` if absent and validate Compose. |
| `make config` | Validate the resolved Compose model. |
| `make up` | Build/start API + PostgreSQL/PostGIS + local LiveKit voice and wait for health. |
| `make up-voice` | Compatibility alias for `make up`. |
| `make up-lan ROADTALK_LAN_HOST=…` | Start the optional home-LAN HTTPS gateway for secure browser-feature testing. |
| `make lan-ca ROADTALK_LAN_HOST=…` | Export the optional local CA certificate for secure test devices. |
| `make up-redis` | Build/start API + database + optional Redis. |
| `make local-url` | Print configured host-local API and docs URLs. |
| `make ps` | Display service health/status. |
| `make logs` | Follow recent service logs. |
| `make verify-database` | Query PostgreSQL and PostGIS versions. |
| `make database-shell` | Open psql. |
| `make redis-cli` | Open redis-cli when the optional profile is running. |
| `make down` | Stop local containers without deleting data. |
| `make down-lan ROADTALK_LAN_HOST=…` | Stop the optional LAN HTTPS stack without deleting data. |
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

## Repairing an older persistent database

Some development database volumes created while Sprint 6 channel work was still in
progress can report revision `0010` while missing the final channel idempotency
columns. The visible symptom is a `500` response from `GET /api/v1/channels` with
`UndefinedColumn: channel.create_idempotency_hash does not exist`.

Migration `0011` reconciles that known drift without deleting accounts, profiles,
locations, channel selections, or other local data. Pull the fixed image and restart:

```sh
docker compose up --build
```

The backend runs `alembic upgrade head` before serving and applies the repair
automatically. Do not run `make reset` for this error unless you intentionally want
to erase all local development data.

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
- the RoadTalk web/API port is LAN-accessible by default and can be restricted with `BACKEND_BIND_ADDRESS`;
- database and Redis ports remain loopback-bound;
- the default stack includes local self-hosted LiveKit and enables the backend media adapter;
- the optional LAN override requires an explicit host IP and resolves an HTTPS gateway for browser secure-context testing;
- backend runs migrations before serving and has a readiness healthcheck;
- browser voice code is checksum-pinned into the backend image and served locally;
- Redis remains optional behind a profile;
- no secret file is committed;
- reset requires explicit confirmation;
- no AWS or LiveKit Cloud resource/call is introduced.
