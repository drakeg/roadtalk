# Premium subscription and entitlement lifecycle

Sprint 14 D04 defines deterministic subscription and entitlement transitions without activating billing.

## Lifecycle

The server-owned lifecycle supports activation, renewal, cancellation, expiry and revocation.

- Activation and renewal require a future expiry.
- Cancellation stops renewal but preserves entitlement only through the already-authorized expiry.
- Expiry cannot be applied before that expiry.
- Revocation removes entitlement immediately.
- Stale transitions and cross-account subscription reuse fail closed.
- Identical event replay is idempotent; conflicting reuse of an event ID fails generically.

## Authorization

Lifecycle receipts are server-authoritative and explicitly preserve existing RoadTalk communication authorization. Premium state does not create or widen account/session/location/proximity/Same-road/channel/convoy/media/moderation eligibility.

## Persistence boundary

D04 uses an in-memory deterministic lifecycle for application logic and CI evidence. It does not claim durable provider-event replay, cross-process concurrency safety, webhook processing or production persistence; those remain later Sprint 14 hardening concerns.

## Provider/cost boundary

No checkout, payment/store provider, payment instrument, provider event, tax logic or recurring service is activated.
