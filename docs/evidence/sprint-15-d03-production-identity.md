# Sprint 15 D03 evidence — Production secrets, identity, and access

Issue: #446  
Requirements: S15-R02, S15-R10, S15-R11  
Acceptance tests: S15-T02, S15-T10, S15-T11

## Implemented

- Added a machine-readable production identity/IAM/secrets contract.
- Requires GitHub Actions OIDC and prohibits shared/static/long-lived CI credentials.
- Scopes future production deployment identity to this repository and main branch; pull-request production deployment is prohibited.
- Requires separate plan/apply roles and manual approval for apply.
- Prohibits administrator policies, wildcard actions/resources, runtime IAM mutation, and unscoped secret reads.
- Requires a managed production secret source under `/roadtalk/production/`.
- Prohibits plaintext secrets in repository, CI logs, and Terraform state.
- Requires secret rotation within 90 days and separate approval for provider credentials.
- Defines MFA-protected, time-bounded, audited, individually attributable break-glass access.
- Adds deterministic CI validation and negative mutation tests.

## Deterministic validation

`python scripts/ci/check-production-identity.py --self-test`

Negative tests prove fail-closed behavior for static CI credentials, long-lived keys, pull-request production deploys, administrator access, wildcard IAM, unscoped secret reads, plaintext repository secrets, excessive rotation windows, break-glass without MFA, shared human users, and false live-evidence claims.

## Not performed or claimed

No production AWS IAM role, GitHub OIDC trust, production secret, provider credential, break-glass session, or production deployment identity was created or exercised. No new recurring spend or production traffic is authorized by D03.

## Acceptance boundary

Merge accepts only the deterministic IAM/secrets/access contract and CI evidence. Live identity provisioning, role-policy verification against real resources, secret rotation exercise, and break-glass exercise remain future live evidence.
