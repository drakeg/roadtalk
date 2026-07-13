#!/bin/sh
set -eu

image="${1:?immutable image URI is required}"
cd /opt/roadtalk
test -f runtime.env
test -f deployment.env

current="$(sed -n 's/^ROADTALK_IMAGE=//p' deployment.env || true)"
if [ -n "$current" ] && [ "$current" != "$image" ]; then
  printf '%s\n' "$current" > previous-image
fi

sed -i '/^ROADTALK_IMAGE=/d' deployment.env
printf 'ROADTALK_IMAGE=%s\n' "$image" >> deployment.env

docker compose --env-file deployment.env pull database api caddy
docker compose --env-file deployment.env up -d database
docker compose --env-file deployment.env run --rm api alembic upgrade head
docker compose --env-file deployment.env up -d api caddy

attempt=0
until curl --fail --silent --show-error http://127.0.0.1/health/ready >/dev/null; do
  attempt=$((attempt + 1))
  [ "$attempt" -lt 30 ] || {
    echo "Deployment health check failed; run rollback.sh."
    exit 1
  }
  sleep 2
done

printf '%s\n' "$image" > current-image
echo "Deployment healthy: $image"
