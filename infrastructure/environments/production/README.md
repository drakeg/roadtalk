# Production Terraform root

Sprint 15 production work is contract-gated. This directory remains non-deploying through S15-D07.

Machine-readable production contracts:

- `production-contract.json` — environment, topology, TLS, immutable artifact, release, and rollback boundaries.
- `identity-contract.json` — CI/CD identity, least privilege, managed secrets, rotation, human access, and break-glass boundaries.
- `observability-contract.json` — health/readiness, structured logging, metrics, alerting, SLO/error-budget, privacy, and release-health boundaries.
- `backup-contract.json` — backup scope, encryption, retention, isolated restore validation, RPO/RTO targets, data protection, and disaster-recovery boundaries.
- `deployment-contract.json` — immutable release inputs, approval, plan binding, migration safety, health-gated rollout, and rollback boundaries.
- `resilience-contract.json` — capacity, rate limits, dependency failure behavior, multi-AZ resilience, graceful degradation, and bounded resource use.

CI validates these contracts with the corresponding `scripts/ci/check-production-*.py` checks.

Production resilience must fail boundedly: concurrency, queues, retries, request sizes, worker
counts, and cache lifetimes cannot grow without limit. Optional-provider failures must degrade
features instead of collapsing core readiness.

D02-D07 do **not** create production infrastructure, live traffic, failover exercises, load
tests, provider activations, or recurring spend. Live capacity and failure-mode evidence remain
separately gated by later Sprint 15 work.

Do not copy single-host field-test assumptions into production.
