# Sprint 9 D08 — Urgent-alert reliability and abuse hardening evidence

## Scope

S09-D08 implements S09-R06, S09-R10 / S09-T06, S09-T10 without pulling Sprint 12 reporting, mute, or moderation scope forward. The urgent-alert path remains explicitly user initiated, server-authorized, short-lived, provider-free, and non-emergency-service.

## Reliability and abuse controls

- `backend/app/notifications/contracts.py` keeps urgent alerts at a maximum ten-minute lifetime and a closed 280-character command contract.
- `backend/app/notifications/service.py` already rejects future/stale payloads, retains bounded idempotency tombstones, rejects changed-payload idempotency collisions, fails closed when the original replay target is deleted, and recomputes current authorization on each composition attempt.
- `backend/app/notifications/limiter.py` adds bounded single-worker field-test rate limits across account, device, network peer, and sender/event idempotency-key dimensions. Event retries are capped independently of the broader account/device/peer budgets.
- `backend/app/api/notifications.py` applies the limiter only after the persistent registered-account gate and before notification composition. Rate-limit responses are generic, return `429` plus `Retry-After`, and disclose no recipient, location, channel-membership, or eligibility information.
- Existing authorization composition continues to derive recipients only from current session, selected-channel, location/proximity, receive-grant, account-status, and notification-preference state. No client recipient, coordinate, radius, route, corridor, or destination targeting is introduced.

## Fail-closed lifecycle evidence

`backend/tests/test_notification_authorization_database.py` locks the current lifecycle behavior: authorized recipients only, preference opt-out, idempotent replay, changed-payload collision rejection, deleted-notification replay rejection, stale-event rejection, revoked-sender-session denial, and deletion cleanup.

`backend/tests/test_notification_limiter.py` locks event retry bounds, independent account/device/peer dimensions, generic rate-limit errors, window expiry, and bounded in-memory bucket storage appropriate to the current single-worker field-test architecture.

External push-provider delivery remains inactive. Therefore provider failure cannot widen authorization or imply delivery/read/response; the product continues to expose only the in-app notification path approved in D06/D07. Delivery, reading, and response are never guaranteed.

## Safety contract

Urgent-alert safety copy remains unchanged and regression-covered: RoadTalk is not an emergency service; delivery is not guaranteed; urgent alerts are user-generated and unverified; and users must contact local emergency services directly when emergency assistance is needed.

## Boundaries and evidence limits

This deliverable adds no APNs/FCM/Expo Push/SNS/Pinpoint/Web Push provider, provider credential, background location/audio permission or collection, AWS/LiveKit Cloud activation, payment method, recurring spend, emergency-services integration, reporting/mute/moderation system, or guaranteed-delivery/read/response claim.

The limiter is intentionally process-local for the approved single-worker field-test design. Distributed/multi-worker enforcement is not claimed and remains outside this named evidence boundary.

## Merge gate

D08 is complete only when backend tests, repository CI, Sprint 7/8 hardening, and Sprint 9 planning gates are green and the PR is merged. Merge closes issue #226 and unlocks S09-D09; it does not authorize external notification providers, recurring spend, production/public beta, emergency-services integration, or Sprint 10 work.
