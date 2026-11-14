# Production Terraform root

Sprint 15 production work is contract-gated. D10 completes deterministic readiness review without authorizing a live deployment.

Machine-readable production contracts:

- `production-contract.json` — environment, topology, TLS, immutable artifact, release, and rollback boundaries.
- `identity-contract.json` — CI/CD identity, least privilege, managed secrets, rotation, human access, and break-glass boundaries.
- `observability-contract.json` — health/readiness, structured logging, metrics, alerting, SLO/error-budget, privacy, and release-health boundaries.
- `backup-contract.json` — backup scope, encryption, retention, isolated restore validation, RPO/RTO targets, data protection, and disaster-recovery boundaries.
- `deployment-contract.json` — immutable release inputs, approval, plan binding, migration safety, health-gated rollout, and rollback boundaries.
- `resilience-contract.json` — capacity, rate limits, dependency failure behavior, multi-AZ resilience, graceful degradation, and bounded resource use.
- `security-privacy-contract.json` — release-blocking security findings, privacy exclusions, credential safety, unsafe configuration, and exception rules.
- `governance-contract.json` — cost, support ownership, legal/privacy review, provider activation, rollback/disable, and exception boundaries.
- `launch-authorization.json` — fail-closed, time-bounded public-beta/live-action authorization record; committed disabled by default.
- `dns-tls-ingress-contract.json` — DNS ownership, TLS, managed ingress, bounded cutover, health, and rollback readiness; live cutover disabled.

CI validates these contracts with the corresponding `scripts/ci/check-production-*.py` checks and the D10 final traceability checker.

Sprint 15 deterministic readiness does **not** authorize production/public-beta traffic, DNS cutover,
provider/store/payment activation, real-money flows, recurring production spend, destructive
changes, or claims of unperformed live load/failover/DR/billing evidence.

See `docs/evidence/sprint-15-d10-final-production-readiness.md` for the Sprint 15 acceptance boundary. Sprint 16 adds executable public-beta preflight gates without changing the default no-launch/no-spend state.
