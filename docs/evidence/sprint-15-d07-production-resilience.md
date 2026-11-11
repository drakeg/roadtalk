# Sprint 15 D07 evidence — Scale, resilience, and failure modes

Issue: #451  
Requirements: S15-R06, S15-R10, S15-R11  
Acceptance tests: S15-T06, S15-T10, S15-T11

## Implemented

- Added a machine-readable production resilience contract.
- Requires documented capacity assumptions, at least 30% design headroom, bounded concurrency,
  bounded queues, and bounded retries.
- Requires public/authenticated rate limiting, burst controls, and Retry-After behavior.
- Requires timeout/backoff/circuit-breaker or fail-fast behavior for remote dependencies.
- Prevents optional dependencies from blocking core readiness.
- Requires multi-AZ database and ingress behavior with bounded failover retries.
- Defines graceful degradation for Premium, notifications, AI, and location providers.
- Requires request/upload, worker, background-job retry, and cache-TTL bounds.
- Adds a future live resilience exercise runbook.
- Adds deterministic CI validation and negative mutation tests.

## Deterministic validation

`python scripts/ci/check-production-resilience.py --self-test`

Negative cases cover single-instance assumptions, unbounded retries, missing rate limits,
rate-limit bypass, missing timeouts, optional-dependency readiness coupling, single-AZ database
or network assumptions, failed graceful degradation, unbounded workers, and false live-failover
claims.

## Not performed or claimed

No live load test, database failover, AZ failure, cache failure, provider-chaos exercise, or
production traffic experiment was performed. No new infrastructure or recurring spend is
authorized by D07.

## Acceptance boundary

Merge accepts deterministic resilience requirements only. Measured capacity, live failover, and
failure-injection evidence remain separately required before production-readiness acceptance.
