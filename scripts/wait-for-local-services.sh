#!/usr/bin/env sh
set -eu

ENV_FILE=${ENV_FILE:-.env}
COMPOSE=${COMPOSE:-docker compose}
TIMEOUT_SECONDS=${LOCAL_WAIT_TIMEOUT_SECONDS:-90}
INTERVAL_SECONDS=2
elapsed=0

[ -f "$ENV_FILE" ] || {
  printf '%s\n' "ERROR: Missing $ENV_FILE. Run 'make setup'." >&2
  exit 1
}

while [ "$elapsed" -lt "$TIMEOUT_SECONDS" ]; do
  database_status=$($COMPOSE --env-file "$ENV_FILE" ps --format json database 2>/dev/null || true)

  if printf '%s' "$database_status" | grep -q '"Health":"healthy"'; then
    printf '%s\n' "PostgreSQL/PostGIS is healthy."
    exit 0
  fi

  sleep "$INTERVAL_SECONDS"
  elapsed=$((elapsed + INTERVAL_SECONDS))
done

printf '%s\n' "ERROR: Local database did not become healthy within $TIMEOUT_SECONDS seconds." >&2
$COMPOSE --env-file "$ENV_FILE" ps >&2 || true
exit 1
