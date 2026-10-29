# Sprint 14 D05 evidence — Premium feature gating

## Deterministic evidence

- Feature policy is centralized in one immutable registry.
- Baseline communication remains available without Premium when existing RoadTalk authorization allows it.
- Premium-only access requires an active, account-matching, non-stale entitlement.
- Premium entitlement never overrides an existing RoadTalk authorization denial.
- Missing, inactive, expired, revoked, stale and cross-account entitlements fail closed.
- Active entitlements without an expiry, observed more than 5 minutes before the gate time, or observed more than 30 seconds in the future fail closed.
- Decisions do not echo entitlement identifiers or expiry.

Validation: `pytest tests/test_premium_gating.py` (15 tests), ruff check/format and mypy clean.
- Decisions expose bounded, server-authoritative audit reasons.

## Requirements covered

- S14-R02 Premium cannot create communication eligibility.
- S14-R05 feature checks are centralized, auditable and fail closed.
- S14-T02 proves Premium entitlement cannot bypass existing authorization.
- S14-T05 proves allow/deny behavior and preserves the non-Premium baseline.

## Evidence exceptions — NOT PERFORMED

No live payment/store provider, checkout, real-money transaction, physical-device purchase, production/public-beta operation, tax/refund/chargeback flow or live provider evidence is claimed.
