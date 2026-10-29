# Premium feature gating

Sprint 14 D05 centralizes Premium feature checks without changing RoadTalk authorization.

## Closed feature policy

The current gate classifies only two surfaces:

- `baseline_communication` — baseline functionality and not Premium-gated.
- `premium_experience` — the Premium-only surface used by the upcoming browser/mobile Premium experience work.

No existing account, session, location, proximity, Same-road, channel, convoy, media or moderation capability is reclassified as Premium.

## Authorization ordering

The feature gate is intentionally downstream of existing RoadTalk authorization.

1. Existing RoadTalk authorization must already allow the action.
2. Baseline features remain allowed without a Premium entitlement.
3. Premium-only features additionally require an active, account-matching, non-stale server entitlement.
4. Premium entitlement can never turn an existing authorization denial into an allow.

## Fail-closed behavior

Premium-only access is denied when the entitlement is missing, inactive, expired, revoked, stale or belongs to another account. Naive timestamps are rejected.

An entitlement is stale when the gate time has reached its expiry, when its server observation is older than `ENTITLEMENT_MAX_OBSERVATION_AGE` (5 minutes), or when it was observed more than `ENTITLEMENT_MAX_FUTURE_SKEW` (30 seconds) after the gate time. A cached entitlement context therefore cannot keep granting Premium after the lifecycle changes; callers re-read the server-owned lifecycle.

An `active` entitlement without an expiry is treated as malformed and denied, because lifecycle activation and renewal always carry a future expiry.

The decision contract is closed and records feature class, entitlement state, reason and server-authoritative provenance for auditability. It does not echo entitlement identifiers or expiry.

## Scope

D05 introduces no checkout, payment/store provider, price, SKU, tax behavior, analytics profile, location expansion or production activation.
