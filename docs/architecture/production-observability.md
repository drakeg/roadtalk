# Production observability and operational health contract

Sprint 15 owner: S15-D04 / #447.

## Health and readiness

Production must expose distinct liveness and readiness semantics. Readiness must verify the database and cache dependencies required for request handling, while optional external integrations must not cause readiness flapping. Health endpoints must not expose secrets or user data.

## Structured logging

Production logs are structured JSON and include request ID, service name, environment, and severity. Raw authorization/cookie headers, secret values, payment data, precise location, and unrelated-user payloads are prohibited.

Retention is bounded to no more than 30 days by this contract unless a separately approved legal/operational requirement establishes a different policy.

## Metrics

The minimum production metric set covers request rate, error rate, latency, dependency health, and resource saturation. Metric labels must not contain user IDs, email addresses, precise location, or other high-cardinality user-specific values.

## Alerts

Every production alert requires an owner, severity, and runbook. Duplicate-storm protection is required. Alerts must not embed secret values or raw user payloads.

## SLO and error budget

The initial readiness contract requires:

- availability target of at least 99.5%;
- p95 request latency target of at most 1000 ms;
- server error rate target of at most 1%;
- explicit error-budget tracking;
- release blocking when the error budget is exhausted.

These are release-readiness targets, not claims of measured production performance.

## Release health gate

A production release path must perform pre-release and post-release health checks, observe health for at least 10 minutes, and require rollback when the health gate fails. Automatic real-user rollout remains prohibited.

## Evidence boundary

D04 CI validation proves observability/privacy invariants only. It does not claim live production metrics, alerts, SLO measurements, or release-health exercises. Live evidence remains required after separately authorized production infrastructure exists.

The machine-readable contract is `infrastructure/environments/production/observability-contract.json`, validated by `scripts/ci/check-production-observability.py`.
