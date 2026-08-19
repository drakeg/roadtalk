# Clean setup

## Scope and cost

This procedure takes a clean checkout to a running local RoadTalk API and mobile
development client. It uses local containers only and creates no AWS or LiveKit
resources or calls.

## Prerequisites

- Git, Make, a POSIX shell, and Docker with Compose v2
- Node.js 22+ and npm for the mobile client
- Xcode/CocoaPods for iOS or Android Studio/JDK for Android development builds
- Python 3.12 only when running backend tooling/tests as host processes

## Procedure

```sh
git clone https://github.com/drakeg/roadtalk.git
cd roadtalk
make prerequisites
make setup
make up
make verify-database
make local-url
```

Review `.env` before starting applications. Its defaults are deliberately local-only;
never reuse them in a shared environment. Change `BACKEND_PORT` if port 8000 is
already occupied; for example `BACKEND_PORT=18000` requires no Compose-file edit.

`make up` is the default local application path. It builds and starts the FastAPI
backend plus PostgreSQL/PostGIS, runs Alembic upgrades before serving, waits for
healthy services, and preserves database data in a named local volume.

Verify the health and version endpoints using the port printed by `make local-url`:

```text
http://127.0.0.1:<BACKEND_PORT>/health/live
http://127.0.0.1:<BACKEND_PORT>/health/ready
http://127.0.0.1:<BACKEND_PORT>/api/v1/system/version
http://127.0.0.1:<BACKEND_PORT>/docs
```

For the mobile client:

```sh
make mobile-install
make mobile-doctor
make mobile-typecheck
make mobile-test
make mobile-ios
# or: make mobile-android
```

The mobile Make targets derive their localhost API endpoint from `BACKEND_PORT` unless
`EXPO_PUBLIC_API_BASE_URL` is explicitly set. A physical device cannot reach the host
through `localhost`; use a LAN-reachable override only for an explicitly intended
local device test and do not expose the API to the public internet.

## Optional host-process backend

Use this only when you specifically need debugger/reload behavior outside Docker:

```sh
docker compose --env-file .env stop backend
make backend-install
make backend-migrate
make backend-migration-check
make backend-test
make backend-run
```

`make backend-run` uses the same `BACKEND_PORT` from `.env`, so the Compose backend
must be stopped first to avoid binding the same port twice.

## Stop and recover

`make down` preserves the named database volume. `make reset CONFIRM_RESET=yes`
irreversibly deletes local database and Redis volumes and is allowed only for
synthetic disposable data. For tool, port, simulator, and network failures, use the
component guides in `backend/README.md`, `mobile/README.md`, and
`local-development.md`.

## Completion checks

- Compose API and PostgreSQL/PostGIS become healthy;
- database and PostGIS verification succeeds;
- configured `BACKEND_PORT` is reflected in the published local API URL;
- Expo Doctor, TypeScript, and mobile tests pass before mobile testing;
- live, ready, and version endpoints return success;
- no untracked `.env`, token, dump, or generated credential is staged for commit.
