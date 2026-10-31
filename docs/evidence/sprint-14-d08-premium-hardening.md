# Sprint 14 D08 evidence — Premium hardening

## Deterministic evidence

- Concurrent identical lifecycle events produce exactly one applied receipt and replay receipts thereafter.
- Conflicting lifecycle event reuse remains generic and fail-closed.
- Premium status reads are bounded independently by account, device and hashed network peer.
- Rate-limit responses are generic and include bounded retry guidance.
- Future webhook payloads are bounded to 64 KiB and stale/future deliveries fail closed.
- Every webhook delivery, including an identical replay, must pass HMAC authenticity.
- Identical authenticated replay is idempotent; conflicting event-ID reuse fails generically.
- Webhook replay storage is bounded and stores only event IDs plus body digests.
- Existing provider failure and stale-entitlement tests continue to prove fail-closed behavior and secret non-disclosure.

## Requirements covered

- S14-R07 / T07: deterministic idempotency, replay and local concurrency behavior.
- S14-R08 / T08: bounded future webhook authenticity/replay boundary without activating a live provider.
- S14-R09 / T09: provider/payment/location/privacy exclusions and non-disclosing failures.
- S14-R11 / T11: no recurring service or provider cost is introduced.

## Evidence exceptions — NOT PERFORMED

No durable distributed replay store, multi-process race test, live Stripe/App Store/Play/other provider webhook, provider secret rotation, provider sandbox, real-money transaction, tax/refund/chargeback flow, physical-device store purchase, production/public-beta operation or provider billing evidence is claimed.
