# Production cost, support, legal, and rollback review

Sprint 15 owner: S15-D09 / #453.

## Cost boundary

D09 does not authorize recurring production spend. Before any launch approval, RoadTalk requires
an explicit production cost model, a named monthly-budget owner, cost alerts, anomaly review,
and separate approval for provider-dependent charges. Unbounded usage-based pricing without a
defined cap or control is not accepted.

## Support ownership

Production requires a named operational owner, incident owner, support contact path, severity
model, escalation path, and runbook index. Production support planning must not assume incidents
occur only during business hours.

## Legal and privacy review

Before launch or provider activation, the project requires review of:
- privacy policy;
- terms of service;
- retention/deletion obligations;
- provider terms;
- app-store policies before store distribution;
- payment/tax obligations before any real-money flow.

D09 does not claim legal-counsel review has occurred and does not make unsupported compliance
claims.

## Provider activation boundary

Premium, payment, and store providers remain disabled by default. Credentials must not be added
before approval, and activation requires named approval. Provider-side billing/store behavior
remains outside this deterministic review until separately accepted.

## Rollback and disable controls

Launch readiness requires a named rollback target, emergency-disable path, provider kill switch,
public-beta disable path, DNS rollback plan, and an explicit named exception for any irreversible
change.

## Exceptions

Any exception requires an owner, reason, expiry, impact statement, and rollback/mitigation plan.
Permanent exceptions are prohibited.

The machine-readable source is
`infrastructure/environments/production/governance-contract.json`, validated by
`scripts/ci/check-production-governance.py`.
