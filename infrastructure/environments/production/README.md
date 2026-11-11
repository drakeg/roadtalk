# Production Terraform root

Sprint 15 production work is contract-gated. This directory remains non-deploying through S15-D06.

Machine-readable production contracts:

- `production-contract.json` — environment, topology, TLS, immutable artifact, release, and rollback boundaries.
- `identity-contract.json` — CI/CD identity, least privilege, managed secrets, rotation, human access, and break-glass boundaries.
- `observability-contract.json` — health/readiness, structured logging, metrics, alerting, SLO/error-budget, privacy, and release-health boundaries.
- `backup-contract.json` — backup scope, encryption, retention, isolated restore validation, RPO/RTO targets, data protection, and disaster-recovery boundaries.
- `deployment-contract.json` — immutable release inputs, approval, plan binding, migration safety, health-gated rollout, and rollback boundaries.

CI validates these contracts with the corresponding `scripts/ci/check-production-*.py` checks.

Production recovery must use encrypted recovery points outside the primary failure domain and
must periodically prove restore integrity in an isolated target. The normal runtime identity
must not be able to erase all backups. Initial RPO/RTO values are targets, not measured claims.

D02-D06 do **not** create production infrastructure, IAM/OIDC resources, monitoring services,
backup services, recovery copies, DNS records, provider credentials, or recurring spend.
Production traffic and live recovery evidence remain separately gated by later Sprint 15 work.

Do not copy the single-host field-test topology or its backup assumptions into production.
