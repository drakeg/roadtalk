# Production Terraform root

Sprint 15 production work is contract-gated. This directory remains non-deploying through S15-D03.

The production root is separate from field test and does not reuse Terraform workspaces,
state, VPCs, hosts, databases, caches, or runtime-secret prefixes.

Machine-readable production contracts:

- `production-contract.json` — environment, topology, TLS, immutable artifact, release, and rollback boundaries.
- `identity-contract.json` — CI/CD identity, least privilege, managed secrets, rotation, human access, and break-glass boundaries.

CI validates these contracts with:

- `scripts/ci/check-production-contract.py`
- `scripts/ci/check-production-identity.py`

Production CI/CD credentials must use short-lived GitHub Actions OIDC federation; shared
static AWS credentials and long-lived access keys are prohibited. Production runtime
secrets belong under `/roadtalk/production/` and must not enter repository content,
CI logs, or Terraform state.

D02/D03 do **not** create production Terraform resources, IAM roles, OIDC trusts, secrets,
DNS records, certificates, provider credentials, or recurring spend. Production/public-beta
traffic and live evidence remain separately gated by later Sprint 15 work.

Do not copy the single-host field-test topology into production.
