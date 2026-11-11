# Sprint 15 D08 evidence — Production security/privacy release gates

Issue: #452  
Requirements: S15-R07, S15-R08, S15-R11  
Acceptance tests: S15-T07, S15-T08, S15-T11

## Implemented

- Added a machine-readable production security/privacy release contract.
- Makes unresolved HIGH/CRITICAL security findings release-blocking.
- Requires dependency, container, filesystem-secret, and IaC scanning.
- Requires production OIDC, secret rotation policy, and least-privilege authorization.
- Prohibits static cloud credentials, shared identities, PR production deployment, and
  cross-environment secret access.
- Prohibits precise location, authorization/cookie headers, payment instruments, unrelated user
  payloads, and user-ID metric labels in telemetry.
- Blocks public database/cache exposure, TLS below 1.2, mutable release artifacts, and plaintext
  secret configuration.
- Requires time-bounded, owned, risk-accepted security/privacy exceptions with compensating controls.
- Adds deterministic CI validation and negative mutation tests.

## Deterministic validation

`python scripts/ci/check-production-security-privacy.py --self-test`

Negative cases cover fail-open release behavior, unresolved high-risk findings, missing container
scan, static credentials, PR deployment, privacy leaks, payment instrument storage, public
database exposure, TLS downgrade, permanent exceptions, and false live-security claims.

## Not performed or claimed

No live penetration test, production security exercise, or live privacy audit was performed.
D08 does not authorize production traffic, provider activation, or recurring spend.

## Acceptance boundary

Merge accepts deterministic security/privacy release gates only. Live security testing and any
external/privacy review required for launch remain separate production-readiness evidence.
