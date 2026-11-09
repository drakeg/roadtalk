# Production identity, IAM, and secret boundaries

Sprint 15 owner: S15-D03 / #446.

## CI/CD identity

Production automation uses GitHub Actions OIDC federation to obtain short-lived AWS sessions. Shared static AWS access keys and long-lived CI credentials are prohibited. Production deployment trust is repository-scoped to `drakeg/roadtalk`, main-branch scoped, and must not allow pull-request jobs to deploy production.

Plan and apply identities are separate. The apply identity requires a manual approval gate and remains unavailable to untrusted pull-request execution.

## Least privilege

Production identities must not use `AdministratorAccess`, wildcard actions, or wildcard resources. Runtime roles cannot modify IAM and cannot read secrets outside the RoadTalk production namespace.

Exact resource/action allowlists are implemented only when the production services are selected and provisioned; D03 defines the fail-closed contract first.

## Runtime secrets

Production secrets come from a managed secret store and use the dedicated `/roadtalk/production/` namespace. Plaintext secret material is prohibited in the repository, GitHub Actions logs, Terraform variables/state, generated artifacts, and documentation.

Applications fetch secrets at runtime through their scoped workload identity. Rotation is required at least every 90 days, with faster rotation where a provider or incident requires it.

External-provider credentials remain separately approved and disabled until their provider plan is accepted.

## Human and break-glass access

Human production access uses individual identities with MFA. Shared users and long-lived access keys are prohibited.

Break-glass access is exceptional, MFA-protected, time-bounded, reason-recorded, audited, and followed by a post-use review. Standing administrator sessions and shared emergency accounts are prohibited.

## Evidence boundary

The D03 contract and CI checks prove policy invariants only. They do not claim that a live AWS OIDC trust, production IAM role, production secret, or break-glass session exists or has been exercised. Those require separately authorized infrastructure and live evidence.

The machine-readable source is `infrastructure/environments/production/identity-contract.json`, validated by `scripts/ci/check-production-identity.py`.
