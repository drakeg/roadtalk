# Clean setup

## Scope and cost

This procedure takes a clean checkout to a running local API and mobile development
client. It uses local containers only and creates no AWS resources.

## Prerequisites

- Git, Make, a POSIX shell, and Docker with Compose v2
- Python 3.12
- Node.js 22 and npm
- Xcode/CocoaPods for iOS or Android Studio/JDK for Android development builds

## Procedure

```sh
git clone https://github.com/drakeg/roadtalk.git
cd roadtalk
make prerequisites
make setup
make up
make verify-database
make backend-install
make backend-migrate
make backend-migration-check
make backend-test
make mobile-install
make mobile-doctor
make mobile-typecheck
make mobile-test
```

Review `.env` before starting applications. Its defaults are deliberately local-only;
never reuse them in a shared environment.

In terminal one:

```sh
make backend-run
```

Verify `http://127.0.0.1:8000/health/live`, `/health/ready`, and
`/api/v1/system/version`. In terminal two, run `make mobile-ios` or
`make mobile-android`. A physical device cannot reach the host through `localhost`;
set `EXPO_PUBLIC_API_BASE_URL` to the development machine's reachable LAN address
before building and do not expose the API to the public internet.

## Stop and recover

`make down` preserves the named database volume. `make reset CONFIRM_RESET=yes`
irreversibly deletes local database and Redis volumes and is allowed only for
synthetic disposable data. For tool, port, simulator, and network failures, use the
component guides in `backend/README.md`, `mobile/README.md`, and
`local-development.md`.

## Completion checks

- database and PostGIS verification succeeds;
- migration drift check and backend tests pass;
- Expo Doctor, TypeScript, and mobile tests pass;
- live, ready, and version endpoints return success;
- no untracked `.env`, token, dump, or generated credential is staged for commit.
