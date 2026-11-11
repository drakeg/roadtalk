# Production Terraform root

Sprint 15 production work is contract-gated. This directory remains non-deploying through S15-D08.

Machine-readable production contracts:

- `production-contract.json` — environment, topology, TLS, immutable artifact, release, and rollback boundaries.
- `identity-contract.json` — CI/CD identity, least privilege, managed secrets, rotation, human access, and break-glass boundaries.
- `observability-contract.json` — health/readiness, structured logging, metrics, alerting, SLO/error-budget, privacy, and release-health boundaries.
- `backup-contract.json` — backup scope, encryption, retention, isolated restore validation, RPO/RTO targets, data protection, and disaster-recovery boundaries.
- `deployment-contract.json` — immutable release inputs, approval, plan binding, migration safety, health-gated rollout, and rollback boundaries.
- `resilience-contract.json` — capacity, rate limits, dependency failure behavior, multi-AZ resilience, graceful degradation, and bounded resource use.
- `security-privacy-contract.json` — release-blocking security findings, privacy exclusions, credential safety, unsafe configuration, and exception rules.

CI validates these contracts with the corresponding `scripts/ci/check-production-*.py` checks.

Production security/privacy gates fail closed. Unresolved HIGH/CRITICAL findings, credential leaks,
unsafe public data services, TLS downgrade, mutable release artifacts, or prohibited telemetry
data block release unless a separately approved time-bounded exception satisfies the contract.

D02-D08 do **not** authorize production traffic, live security testing, provider activation, or
recurring spend. Live launch evidence remains separately gated by later Sprint 15 work.
