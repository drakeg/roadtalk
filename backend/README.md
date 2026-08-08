# Backend

Sprint 5 active owner: S05-D06 Revocation and lifecycle reconciliation.

The backend is a Python/FastAPI modular-monolith control API.

## Current foundation

S01-D03 and S01-D04 provide:

- typed environment configuration
- privacy-safe JSON logging
- request correlation IDs
- RFC 9457-style problem responses
- liveness, readiness, and version endpoints
- extensible readiness-check registry
- automated foundation tests
- SQLAlchemy account, device, session, and optional one-to-one profile models
- Alembic migrations with PostGIS enablement
- database readiness checks
- anonymous account/device registration
- short-lived device-bound access tokens
- hashed rotating refresh credentials, logout, device revocation, and replay-family revocation

Profile persistence supports an incomplete identity without inventing a callsign or avatar. S02-D04 adds owner-scoped profile reads and conditional callsign updates using the shared policy. Avatar mutation is validated against the bundled catalog, and optional anonymous recovery remains PII-free.

S03-D02 adds persistence only for append-only foreground-location consent decisions
and one expiring PostGIS geography point per account. The current row is owned by the
account and source device, contains quality/sequence/expiry metadata, and cascades on
account or source-device deletion. No location API, mobile permission, background
collection, history table, cache, map, or nearby response is implemented in D02.

S03-D03 adds a versioned server-side domain policy for coordinate shape, accuracy,
observation time, optional heading/speed, device ownership, current consent,
same-device sequencing, cross-device replacement, plausible movement, and bounded
expiry. Accepted writes return metadata only; policy failures use stable messages that
do not disclose submitted coordinates, movement, or internal thresholds. Explicit and
expired-row deletion helpers are idempotent and require no background scheduler for
correctness.

Mutation and future nearby-read limiters cover peer, account, and device dimensions in
the existing API process. They are deliberately process-local for the approved
single-worker field-test architecture. A multi-worker deployment must introduce a
separately approved shared design; it must not silently weaken these controls.

S03-D04 exposes owner-scoped authenticated consent and current-location mutations.
Consent grants require the exact active policy and disclosure versions; withdrawal
never requires accepting a newer version and atomically removes the current row.
Location writes pass through the D03 policy and return metadata only. Pause is
idempotent, and every mutation shares the bounded peer/account/device limiter.

S03-D05 adds one caller-relative nearby summary. It requires the caller and every
eligible candidate to have a fresh, usable current row under the active consent
policy, excludes the caller, and evaluates the configured radius with the existing
GiST-indexed PostGIS `ST_DWithin` predicate. The response contains only availability,
a `none`/`few`/`many` bucket, freshness, and the caller's expiry boundary. Exact
counts, thresholds, identities, coordinates, distances, and bearings remain private.

S04-D03 adds authenticated receive-only PTT grant creation and release. Ownership,
the controlled room, opaque participant reference, provider scope, policy, and TTL
are server-derived. Only SHA-256 idempotency metadata is persisted; the raw key and
one-time participant token are never stored or logged. Replays return the original
grant metadata without another credential. A bounded process-local limiter covers
peer, account, and device dimensions, while the live provider remains disabled.

S04-D04 adds nested transmit authorization for an active caller-owned receive grant.
The server alone selects the existing opaque participant, microphone-only scope,
policy, and expiry. Provider promotion must succeed before local authorization is
committed; ambiguous outcomes roll back locally and attempt immediate deny
reconciliation. Release, expiry, receive release, logout, and device revocation
invalidate publication without a worker or scheduler.

S04-D07 makes ambiguous provider state durably fail closed. A failed promotion revokes
its parent receive grant and attempts both microphone denial and participant removal.
Delayed release, refresh replay, logout, and device revocation mark all related local
media grants revoked before any later provider cleanup. A bounded, explicitly invoked
reconciliation helper processes expired or cleanup-pending metadata with an injected
provider; it is not scheduled and creates no queue, worker, network call, or cloud
resource in CI. Dedicated privacy gates reject live credentials/network adapters,
paid or background media features, sensitive logs/evidence, non-metadata columns, and
Sprint 5/6 drift.

S05-D02 adds a versioned server-only proximity policy and a private authorization
query over the existing PostGIS location and media-grant tables. The sender location
and every candidate location must remain usable through the complete 30-second
delivery window. Candidates also require same-device location ownership, an active
account/session/receive grant through that window, the controlled room, current
consent, the current policies, and the inclusive GiST-backed `ST_DWithin` predicate.
The query returns only transient opaque grant/account/device/participant references
to the authorization service; it adds no API, persistence, migration, provider call,
worker, cache, AWS resource, or recurring cost.

S05-D03 integrates that private query into transmit creation after caller-owned
receive-grant and concurrency checks and before any transmit persistence or microphone
promotion. Missing usable sender location fails as `PTT_LOCATION_UNAVAILABLE`; an
empty audience fails as `PTT_NO_NEARBY_LISTENERS`. Recipient membership remains
transient process memory and is neither returned nor stored. The API shape, provider
boundary, disabled defaults, and $0 infrastructure posture remain unchanged.

S05-D04 extends only the typed media-provider boundary and deterministic fake.
Receive credential requests make automatic subscription explicitly false. Opaque
track lookup returns a verified value only when room, publishing participant,
microphone source, and active state match. Selective subscribe/unsubscribe requests
accept that verified track plus sorted unique opaque participant references; replay is
idempotent and injected failures occur before fake state mutation. No route, database
change, production adapter, provider SDK/call, AWS resource, or recurring cost is
introduced.

S05-D05 adds the authenticated nested publication handshake. Its request accepts only
one opaque track reference. The service binds that reference to the caller-owned
active transmit room and participant, requires an active microphone publication,
recomputes current proximity eligibility, and sends only a sorted unique opaque
participant set to the selective-subscription boundary. Replay is metadata-only;
conflicting tracks fail closed. Storage adds only the verified track reference,
proximity policy version, evaluation timestamp, and semantic delivery outcome. No
audience membership, coordinate, distance, count, provider payload, live adapter,
cloud resource, or recurring cost is added.

S05-D06 adds bounded synchronous fail-closed reconciliation after location
replacement/withdrawal, consent withdrawal, logout, refresh/session/device
revocation, account recovery, receive/transmit release, expiry, and injected provider
failure. Each active published transmit is marked reconciling before provider work;
eligibility is recomputed from current source-of-truth rows, newly ineligible opaque
participants are unsubscribed, and empty or uncertain audiences disable publication.
Release unsubscribes the verified track before revoking microphone authority.
Recipient references remain bounded process-local values only. No membership table,
scheduler, worker, queue, Redis, WebSocket, live provider call, AWS resource, or
recurring cost is added.

## Local setup

From the repository root:

```sh
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -e 'backend[dev]'
make up
make backend-migrate
make backend-migration-check
make backend-test
make backend-run
```

The API listens on `127.0.0.1:8000` by default.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health/live` | Process liveness. |
| `GET /health/ready` | Registered dependency readiness. |
| `GET /api/v1/system/version` | API version and environment. |
| `GET /docs` | Local OpenAPI UI when enabled. |
| `POST /api/v1/auth/anonymous` | Register an anonymous account and device session. |
| `POST /api/v1/auth/refresh` | Rotate a refresh credential and issue a new token pair. |
| `GET /api/v1/auth/session` | Validate the current access token/session. |
| `POST /api/v1/auth/logout` | Revoke the current session. |
| `DELETE /api/v1/auth/devices/{device_id}` | Revoke all active sessions for an owned device. |
| `GET /api/v1/callsigns/availability?callsign=...` | Authenticated, rate-limited callsign check. |
| `POST /api/v1/me/recovery-key` | Create or rotate an authenticated account recovery key. |
| `POST /api/v1/sessions/recover` | Transfer an anonymous account and establish a replacement session. |
| `GET /api/v1/me/profile` | Read the authenticated account's private setup state and minimal public identity. |
| `PATCH /api/v1/me/profile` | Conditionally update the authenticated account's callsign. |
| `PUT /api/v1/me/location-consent` | Grant the current foreground-location policy and disclosure. |
| `DELETE /api/v1/me/location-consent` | Withdraw consent and atomically remove current location. |
| `PUT /api/v1/me/location` | Submit one validated current foreground sample; response omits coordinates. |
| `DELETE /api/v1/me/location` | Idempotently pause/remove the authenticated account's current sample. |
| `GET /api/v1/nearby/summary` | Return only caller-relative availability, coarse bucket, freshness, and caller expiry. |
| `POST /api/v1/ptt/grants` | Create a receive-only grant for the server-controlled opaque room. |
| `POST /api/v1/ptt/grants/{receive_grant_id}/transmit` | Promote an owned active participant to microphone-only publication for at most 30 seconds. |
| `POST /api/v1/ptt/grants/{transmit_grant_id}/publication` | Verify one opaque microphone track and apply the current server-derived nearby audience. |
| `DELETE /api/v1/ptt/grants/{grant_id}` | Idempotently release an owned receive or transmit grant. |

## Checks

```sh
make backend-format-check
make backend-lint
make backend-typecheck
make backend-test
ROADTALK_RUN_DATABASE_TESTS=1 make backend-test  # migrated disposable database only
```

## Location control boundary

S03-D05 keeps all four private mutations and adds only the coarse authenticated nearby
summary listed above. It does not add a coordinate read route, mobile permission
request, collection lifecycle, maps, history, nearby identities, background jobs,
analytics, or location logging. Account, device, and platform ownership come only
from the verified bearer session; request bodies cannot select them. Consumer GPS
remains non-authoritative and is not cryptographic proof of position; freshness,
accuracy, sequence, and movement checks reduce obvious bad input but cannot eliminate
spoofing.

The implementation reuses the current API process and PostgreSQL/PostGIS database.
It adds no Terraform or AWS resources and requires no RDS, managed Redis, NAT Gateway,
load balancer, container service, or scheduler. Expected incremental AWS cost is $0.

## Identity scope boundary

S02-D04 exposes only the authenticated account at `/api/v1/me/profile`; callers cannot
select another account. Version `0` represents an uninitialized profile, and every
write must supply the current version. Stale writes, unknown fields, callsign
collisions, and cooldown violations fail closed. The reusable public identity DTO
contains only display callsign and bundled-avatar identifier. Avatar changes remain
read-only until S02-D05 supplies catalog validation. No AWS resources, Terraform
changes, or managed services are added.


## Anonymous recovery

S02-D07 adds optional recovery without email, SMS, passwords, or hosted identity.
A recovery key contains a non-secret random lookup selector and at least 256 bits of
secret entropy. The server stores the selector plus only a salted, versioned scrypt
hash of the complete key, protected by a separate application pepper.

Creating or rotating a key returns plaintext once. Successful recovery atomically
rotates the key, revokes every existing account session, transfers an eligible fresh
installation, and creates a replacement session. Invalid, unknown, and replayed keys
share the same failure response. Abuse controls are bounded and process-local for the
current single-worker field-test design; direct peer address, installation, selector,
account, and device dimensions are checked without logging their values.

Recovery material must never enter logs, analytics, URLs, ordinary storage, or support
workflows. A multi-worker deployment requires a separately approved shared rate-limit
design. This implementation adds no AWS resources or managed cache.
