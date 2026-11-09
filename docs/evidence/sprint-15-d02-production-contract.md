# Sprint 15 D02 evidence — Production environment/deployment contract

Issue: #445  
Requirements: S15-R01, S15-R05, S15-R10, S15-R11  
Acceptance tests: S15-T01, partial S15-T05, S15-T10, S15-T11

## Implemented

- Added a machine-readable production contract at `infrastructure/environments/production/production-contract.json`.
- Defined explicit environment/state/secret separation from field test.
- Defined a multi-AZ private target topology and prohibited single-host/public database/cache production operation.
- Defined approved-input domain ownership, TLS >=1.2, HTTPS redirect, and certificate-validation requirements.
- Required digest-pinned backend artifacts, provenance, SBOM evidence, and a named rollback artifact.
- Kept production deployment, public beta, DNS cutover, recurring spend, Premium/payment/store providers, and automatic real-user rollout unauthorized.
- Defined exact-plan/exact-artifact/manual-approval/migration/rollback/emergency-disable release invariants.
- Added deterministic CI validation plus negative mutation tests.

## Deterministic validation

`python scripts/ci/check-production-contract.py --self-test`

The checker validates the committed contract and proves representative unsafe mutations fail closed, including ambiguous environment names, production authorization, field-test workspace reuse, single-host topology, public database exposure, TLS 1.1, mutable artifacts, plaintext CI secrets, automatic rollout, and false production-evidence claims.

## Not performed or claimed

No AWS production resources were created or changed. No Terraform production apply, DNS change, certificate issuance, public-beta launch, real-user traffic, production database migration, live load test, live failover, disaster-recovery exercise, production backup restore, provider/store/payment activation, production billing, or live rollback was performed.

The topology is a contract for later implementation, not evidence that the topology exists.

## Rollback

Revert the D02 PR. Because D02 creates no production resources and authorizes no deployment, rollback has no infrastructure side effects.

## Acceptance boundary

Merge accepts only the deterministic production environment/deployment contract. It does not authorize production traffic, recurring spend, provider activation, DNS cutover, destructive changes, or claims of live production evidence.
