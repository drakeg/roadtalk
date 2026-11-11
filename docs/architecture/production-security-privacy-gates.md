# Production security and privacy release gates

Sprint 15 owner: S15-D08 / #452.

## Release policy

Production release approval fails closed. Any unresolved HIGH or CRITICAL dependency,
container, filesystem-secret, or IaC finding blocks release unless a separately reviewed,
time-bounded exception exists.

Security and privacy exceptions require an owner, rationale, expiry, explicit risk acceptance,
and compensating control. Permanent exceptions are not accepted by the D08 contract.

## Security checks

The production release gate requires:
- Python dependency auditing;
- mobile dependency auditing;
- container vulnerability scanning;
- filesystem secret scanning;
- IaC misconfiguration scanning;
- immutable release artifacts;
- production OIDC rather than static cloud credentials;
- least-privilege production authorization.

Existing CI scanners remain the implementation foundation. D08 binds their results to release
acceptance rather than treating them as informational only.

## Privacy gates

Production telemetry and configuration must continue to exclude precise location, raw
authorization/cookie headers, payment instruments, unrelated user payloads, and user-specific
metric labels. Existing privacy regression checks remain mandatory release inputs.

## Unsafe configuration

Production database/cache exposure, TLS below 1.2, mutable deployment artifacts, plaintext secret
configuration, pull-request production deployment, and cross-environment secret access are all
release-blocking conditions.

## Evidence boundary

D08 validates deterministic release-policy invariants only. It does not claim a live penetration
test, production security exercise, or live privacy audit.

The machine-readable contract is
`infrastructure/environments/production/security-privacy-contract.json`, validated by
`scripts/ci/check-production-security-privacy.py`.
