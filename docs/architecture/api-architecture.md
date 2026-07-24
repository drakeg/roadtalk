# RoadTalk API Architecture

- Status: Approved for Sprint 1 implementation
- Sprint: 0
- Requirements: S00-R03
- Acceptance: S00-T02
- Issue: #5
- Date: 2026-07-12

## Contract principles

- Base path: `/api/v1`
- JSON over HTTPS for REST.
- WebSocket endpoint: `/api/v1/events`.
- UTC timestamps use RFC 3339.
- Identifiers are server-generated UUIDs and are opaque to clients.
- OpenAPI is the REST contract; a versioned JSON Schema catalog is the event contract.
- Clients send `X-Request-ID`; the server generates one when absent.
- Retry-prone mutations use `Idempotency-Key`.
- Access tokens are short-lived. Refresh credentials use secure platform storage and rotation.
- Authentication proves a session; authorization is evaluated per resource and action.
- Exact coordinates never appear in other-user payloads.
- Media credentials are returned only by a dedicated, authorized grant endpoint and expire quickly.

## Response envelope

Successful single-resource responses return the resource directly. Collections use:

```json
{
  "items": [],
  "next_cursor": null
}
```

Errors use RFC 9457-style problem details:

```json
{
  "type": "https://roadtalk.example/problems/location-stale",
  "title": "Location is stale",
  "status": 409,
  "code": "LOCATION_STALE",
  "detail": "A current location is required for this action.",
  "request_id": "uuid",
  "errors": []
}
```

No stack traces, secrets, media tokens, exact coordinates, or internal identifiers appear in errors.

## Versioning

- Backward-compatible additions remain in `v1`.
- Removing or changing established semantics requires a new major API version.
- Event payloads carry `schema_version`.
- Mobile clients advertise `client_version`, platform, and supported event-schema versions.
- The server may reject unsupported versions with a stable upgrade-required problem.
- Deprecations are documented with announcement, telemetry, and removal dates.

## Authentication lifecycle

| Endpoint | Method | Purpose |
|---|---|---|
| `/sessions/anonymous` | POST | Create an anonymous account/session and registered device. |
| `/sessions/refresh` | POST | Rotate refresh credentials and issue a new access token. |
| `/sessions/current` | DELETE | Revoke the current session. |
| `/devices/{device_id}` | DELETE | Revoke a device and its sessions. |
| `/account` | DELETE | Begin verified account deletion and return deletion state. |

Anonymous account recovery details are finalized in Sprint 2. Sprint 1 implements only the foundation required by its approved scope.

## MVP resource groups

### Profile and identity

| Endpoint | Methods | Notes |
|---|---|---|
| `/me` | GET, PATCH | Private account representation and allowed preferences. |
| `/me/profile` | GET, PATCH | Callsign/avatar/public-profile fields after Sprint 2. |
| `/callsigns/availability` | GET | Normalized availability check; rate limited. |

### Location and presence

| Endpoint | Methods | Notes |
|---|---|---|
| `/me/location` | PUT, DELETE | Upsert current sample or withdraw location consent/presence. |
| `/me/presence` | PUT, DELETE | Foreground/background/away state with expiry. |
| `/nearby/summary` | GET | Counts and coarse awareness only; no coordinates. |

Location update request fields:

- client timestamp
- latitude/longitude
- horizontal accuracy
- optional heading and speed
- collection mode: foreground or background
- monotonic client sequence
- consent-policy version

Server validation covers range, freshness, accuracy, sequence, plausible movement, session ownership, consent, and rate limits.

### Channels

| Endpoint | Methods | Notes |
|---|---|---|
| `/channels` | GET | Available approved channels. |
| `/channels/{channel_id}/join` | POST | Idempotent membership/selection. |
| `/channels/{channel_id}/leave` | POST | Idempotent leave. |
| `/me/channel` | GET | Current selection. |

Private channels are not implemented until Sprint 6.

### Push-to-talk and media authorization

| Endpoint | Method | Purpose |
|---|---|---|
| `/ptt/grants` | POST | Create an authenticated receive-only grant for the opaque controlled room; server derives ownership, room, participant, scope, policy, and TTL. |
| `/ptt/grants/{grant_id}` | DELETE | Idempotently release the caller/device-owned receive grant and remove its participant. |
| `/ptt/transmissions/{transmission_id}/feedback` | POST | Record technical outcome or later moderation reference; never audio. |

Grant response includes:

- opaque grant and room identifiers
- LiveKit URL
- short-lived participant token
- allowed publish/subscribe actions
- expiry
- policy version
- reconnect rules

It excludes participant coordinates and server/media secrets.

## WebSocket event architecture

Connection:

1. Client opens `wss://.../api/v1/events` with a short-lived access token using the approved transport mechanism.
2. Server validates the session and device.
3. Client sends `client.ready` with schema and capability versions.
4. Server sends `session.ready` and a heartbeat interval.
5. Missed heartbeats expire presence and connection ownership.

Event envelope:

```json
{
  "event_id": "uuid",
  "type": "presence.changed",
  "schema_version": 1,
  "occurred_at": "2026-07-12T05:00:00Z",
  "sequence": 42,
  "data": {}
}
```

MVP event groups:

- `session.ready`, `session.revoked`, `session.policy_changed`
- `presence.changed`, `nearby.summary_changed`
- `channel.changed`
- `ptt.grant_revoked`, `ptt.transmission_available`, `ptt.transmission_ended`
- `system.degraded`, `system.recovered`, `client.upgrade_required`

Events are at-least-once where replay is supported. Clients deduplicate by `event_id` and order a connection stream by `sequence`. Durable state is re-read over REST after reconnect; the event stream is not the durable source of truth.

## Authorization order for transmit

1. active, non-revoked session
2. accepted current policy/consent versions
3. non-expired presence and usable location
4. channel eligibility
5. mute/block/moderation policy
6. rate and concurrency limits
7. proximity policy
8. media service availability
9. least-privilege token issuance

Any unknown foundational state fails closed.

## Idempotency and concurrency

- Anonymous-session creation, channel changes, grant creation, feedback, and deletion requests accept idempotency keys.
- Keys are scoped to account, route, and normalized request hash.
- Reusing a key with a different body returns a conflict.
- PTT stores only a SHA-256 key digest and normalized-request fingerprint. The raw
  key and one-time participant token are never persisted or logged; successful replay
  returns the original metadata without reissuing credentials.
- Location updates use client sequence plus server version; older samples are rejected.
- Mutable resources carry `version` and support conditional updates.
- PTT uses one active publishing grant per account/device unless a later requirement changes it.

## Rate-limit dimensions

- IP/network reputation
- account and device
- route/action
- callsign normalization
- location update frequency
- grant attempts and active grants
- WebSocket connects and messages

Responses use `429`, a stable problem code, and `Retry-After`. Limits are server-configurable and must not disclose precise abuse thresholds publicly.

## Required tests

- OpenAPI schema validation
- event-schema validation and compatibility
- authentication and per-action authorization matrices
- idempotency replay and conflict behavior
- stale/out-of-order/implausible location samples
- blocked/muted/cross-channel/out-of-radius grant denial
- token scope and expiration
- WebSocket connect, heartbeat, deduplication, reconnect, and revoked session
- log inspection for sensitive-data leakage

## Primary references

- [FastAPI OpenAPI](https://fastapi.tiangolo.com/tutorial/metadata/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [FastAPI WebSocket testing](https://fastapi.tiangolo.com/advanced/testing-websockets/)
- [LiveKit tokens and grants](https://docs.livekit.io/frontends/reference/tokens-grants/)
