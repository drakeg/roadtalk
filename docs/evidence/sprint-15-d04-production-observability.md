# Sprint 15 D04 evidence — Production observability and operational health

Issue: #447  
Requirements: S15-R03, S15-R08, S15-R11  
Acceptance tests: S15-T03, S15-T08, S15-T11

## Implemented

- Added a machine-readable observability/health contract.
- Requires separate liveness/readiness semantics and dependency-aware readiness.
- Prohibits secrets/user data in health endpoints.
- Requires structured JSON logging with request/service/environment/severity context.
- Prohibits authorization headers, cookies, secrets, payment data, precise location, and unrelated-user payloads in logs.
- Requires bounded log retention.
- Requires request-rate, error-rate, latency, dependency-health, and saturation metrics.
- Prohibits user-specific/high-cardinality metric labels.
- Requires alert ownership, severity, runbooks, duplicate-storm protection, and privacy-safe alert content.
- Defines initial availability/latency/error-rate SLO targets and an error-budget release gate.
- Requires pre/post-release health checks, observation window, and rollback on failed health.
- Adds deterministic CI validation and negative mutation tests.

## Deterministic validation

`python scripts/ci/check-production-observability.py --self-test`

The negative suite verifies fail-closed behavior for missing readiness, user-data health leakage, authorization-header logging, precise-location logging, user-ID metric labels, unbounded cardinality, ownerless alerts, secret-bearing alerts, missing error budgets, automatic rollout, and false live-evidence claims.

## Not performed or claimed

No live production metrics were collected, no production alert fired, no production SLO was measured, no production release-health gate was exercised, and no production monitoring service was provisioned. D04 does not authorize recurring spend or real-user traffic.

## Acceptance boundary

Merge accepts only deterministic observability, privacy, and release-health invariants. Live dashboards, alert delivery, measured SLOs, incident response, and production release-health evidence remain future work.
