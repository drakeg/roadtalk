#!/usr/bin/env sh
set -eu

fail() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || fail "Docker is required. Install Docker Desktop or Docker Engine."
docker info >/dev/null 2>&1 || fail "Docker is installed but the daemon is not available."
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required as the 'docker compose' plugin."

printf '%s\n' "Docker prerequisites are available."
