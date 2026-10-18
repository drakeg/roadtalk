# Sprint 14 D04 evidence — subscription and entitlement lifecycle

## Deterministic evidence

- Activation and renewal produce active server-authoritative entitlement.
- Cancellation preserves entitlement only until the existing expiry.
- Expiry fails closed if attempted early and removes entitlement at expiry.
- Revocation removes entitlement immediately.
- Stale events and cross-account subscription transitions fail closed.
- Identical event replay returns an idempotent replay receipt.
- Conflicting reuse of an event ID fails generically.
- Lifecycle event schemas are closed and reject payment/provider over-posting.

## Requirements covered

- S14-R04 subscription and entitlement lifecycle semantics.
- S14-R07 deterministic event idempotency/replay behavior.
- S14-R09 payment/provider data remains outside lifecycle payloads.
- S14-R11 incremental recurring implementation cost remains $0.

## Evidence exceptions — NOT PERFORMED

No durable cross-process replay store, database race testing, live provider/store event, webhook, checkout, real-money transaction, tax/refund/chargeback flow, physical-device store purchase, production/public-beta operation or provider billing evidence is claimed.
