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
| RoadTalk FastAPI | `http://127.0.0.1:8000` | `make up` |
| PostgreSQL 17 + PostGIS 3.5 | `127.0.0.1:5432` | `make up` |
| LiveKit (local voice) | `ws://127.0.0.1:7880` | `make up` |
| Redis 8 | `127.0.0.1:6379` | `make up-redis` |

HTTP and database ports bind only to loopback. LiveKit's local WebRTC transport also
publishes its TCP/UDP media ports so browsers and devices can establish audio. Redis
is optional and excluded from the default Compose profile.

## Testing from another device on your home network

The default stack intentionally binds the web application to loopback. For an explicit,
temporary home-LAN test, find this computer's private IPv4 address and run:

```sh
make up-lan ROADTALK_LAN_HOST=10.0.0.25
make lan-ca ROADTALK_LAN_HOST=10.0.0.25
```

Replace `10.0.0.25` with the Docker host's actual private address. The LAN workflow
adds a Caddy HTTPS gateway at `https://10.0.0.25:8443/` and routes both the RoadTalk
API and LiveKit signaling through it. HTTPS is required because browsers do not grant
microphone or precise-location access to an ordinary insecure private-IP origin.

Caddy's local certificate authority is exported to
`.local/roadtalk-local-ca.crt`. Securely copy that certificate to each test device,
install it as a trusted root, and explicitly enable full trust where the operating
system requires it. Do not copy or trust any other file from the Caddy data volume.
Restart the device browser after changing certificate trust.

Your host firewall must permit the following inbound traffic from the trusted home
subnet only:

| Protocol | Port | Purpose |
|---|---:|---|
| TCP | 8443 | RoadTalk HTTPS and LiveKit secure signaling |
| TCP | 7881 | LiveKit WebRTC fallback |
| UDP | 7882 | LiveKit WebRTC media |

Do not configure router port forwarding, public DNS, or internet exposure. The gateway
uses local development credentials and is suitable only for a private, trusted test
network. Stop LAN exposure when testing is complete:

```sh
make down-lan ROADTALK_LAN_HOST=10.0.0.25
```

The normal `docker compose up --build` and `make up` workflows remain loopback-only.

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
| `make up` | Build/start API + PostgreSQL/PostGIS + local LiveKit voice and wait for health. |
| `make up-voice` | Compatibility alias for `make up`. |
| `make up-lan ROADTALK_LAN_HOST=…` | Start the opt-in home-LAN HTTPS gateway. |
| `make lan-ca ROADTALK_LAN_HOST=…` | Export the local CA certificate for test devices. |
| `make up-redis` | Build/start API + database + optional Redis. |
| `make local-url` | Print configured API and docs URLs. |
| `make ps` | Display service health/status. |
| `make logs` | Follow recent service logs. |
| `make verify-database` | Query PostgreSQL and PostGIS versions. |
| `make database-shell` | Open psql. |
| `make redis-cli` | Open redis-cli when the optional profile is running. |
| `make down` | Stop loopback-only containers without deleting data. |
| `make down-lan ROADTALK_LAN_HOST=…` | Stop the LAN HTTPS stack without deleting data. |
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
- the default stack includes local self-hosted LiveKit and enables the backend media adapter;
- the LAN override requires an explicit host IP, resolves an HTTPS gateway, and keeps the normal stack loopback-only;
- backend runs migrations before serving and has a readiness healthcheck;
- browser voice code is checksum-pinned into the backend image and served locally;
- Redis remains optional behind a profile;
- no secret file is committed;
- reset requires explicit confirmation;
- no AWS or LiveKit Cloud resource/call is introduced.
