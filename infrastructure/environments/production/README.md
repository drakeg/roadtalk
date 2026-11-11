# Production Terraform root

Sprint 15 production work is contract-gated. This directory remains non-deploying through S15-D09.

Machine-readable production contracts:

- `production-contract.json` — environment, topology, TLS, immutable artifact, release, and rollback boundaries.
- `identity-contract.json` — CI/CD identity, least privilege, managed secrets, rotation, human access, and break-glass boundaries.
- `observability-contract.json` — health/readiness, structured logging, metrics, alerting, SLO/error-budget, privacy, and release-health boundaries.
- `backup-contract.json` — backup scope, encryption, retention, isolated restore validation, RPO/RTO targets, data protection, and disaster-recovery boundaries.
- `deployment-contract.json` — immutable release inputs, approval, plan binding, migration safety, health-gated rollout, and rollback boundaries.
- `resilience-contract.json` — capacity, rate limits, dependency failure behavior, multi-AZ resilience, graceful degradation, and bounded resource use.
- `security-privacy-contract.json` — release-blocking security findings, privacy exclusions, credential safety, unsafe configuration, and exception rules.
- `governance-contract.json` — cost, support ownership, legal/privacy review, provider activation, rollback/disable, and exception boundaries.

CI validates these contracts with the corresponding `scripts/ci/check-production-*.py` checks.

Production/public-beta launch remains blocked until cost ownership, support ownership, legal/privacy
review, provider boundaries, rollback/disable controls, and named exceptions are explicitly
accepted. Provider credentials and recurring spend remain separately gated.

D02-D09 do **not** authorize production traffic, public beta, DNS cutover, provider activation,
real-money flows, or recurring spend.
