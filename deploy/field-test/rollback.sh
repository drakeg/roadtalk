#!/bin/sh
set -eu

cd /opt/roadtalk
previous="$(cat previous-image)"
test -n "$previous"

sed -i '/^ROADTALK_IMAGE=/d' deployment.env
printf 'ROADTALK_IMAGE=%s\n' "$previous" >> deployment.env
docker compose --env-file deployment.env pull api
docker compose --env-file deployment.env up -d api caddy
curl --fail --retry 20 --retry-delay 2 http://127.0.0.1/health/ready >/dev/null
printf '%s\n' "$previous" > current-image
echo "Rollback healthy: $previous"
