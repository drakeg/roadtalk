# Premium replay, webhook, abuse and privacy hardening

Sprint 14 D08 hardens the deterministic Premium boundary without activating a payment or store provider.

## Lifecycle replay and concurrency

The in-memory Premium lifecycle serializes reads and transitions with a re-entrant lock. Identical concurrent events are applied once and subsequent deliveries return replay receipts. Conflicting reuse of an event ID remains a generic failure.

This is intentionally local/CI evidence. It does not claim cross-process or durable production replay guarantees.

## Premium status abuse control

Authenticated Premium status reads are bounded independently by account, device and network peer. Peer identifiers are hashed before limiter storage. Limits fail with one generic 429 response and a bounded Retry-After; no account/provider state is disclosed.

The limiter remains downstream of normal RoadTalk authentication and cannot create communication eligibility.

## Future webhook boundary

D08 adds no webhook route and configures no live provider secret. The local/test boundary demonstrates the requirements a future provider integration must satisfy:

- HMAC-SHA256 authenticity on every delivery, including replay.
- Closed event identity supplied separately from the bounded raw body.
- Maximum 64 KiB payload.
- Five-minute age window with 30-second future-skew tolerance.
- Identical replay is idempotent only after signature verification.
- Conflicting event-ID reuse fails generically.
- Replay storage is bounded.

No provider credential, signature or raw body is persisted in application state beyond the bounded in-memory replay digest used by the deterministic test boundary.

## Privacy and non-enumeration

Premium status responses remain caller-only, short-lived and no-store. Provider failures, rate limits, webhook failures and lifecycle conflicts use stable generic messages. No card/bank data, tax identifiers, provider credentials, raw location/route history, unrelated-user data, recovery material, or analytics/marketing profiles are introduced.

## Cost and activation boundary

Incremental recurring implementation cost remains $0. There is no live checkout, webhook route, payment/store SDK, tax collection, production provider, or recurring external service.
