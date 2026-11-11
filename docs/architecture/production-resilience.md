# Production scale, resilience, and failure-mode hardening

Sprint 15 owner: S15-D07 / #451.

## Capacity model

Production requires an explicit capacity model with at least 30% headroom, bounded concurrency,
bounded queue depth, and no assumption that a single instance can absorb normal production
traffic. Capacity thresholds are design inputs until measured live load testing is authorized.

## Rate limiting and abuse resistance

Public and authenticated APIs require rate limiting, per-identity burst limits, and clear
Retry-After semantics. Rate-limit bypass defaults to denied. Limits must be tuned with measured
traffic later; D07 defines the invariant, not final throughput numbers.

## Dependency failure behavior

Every remote dependency requires timeouts, bounded retries with exponential backoff, and
circuit-breaker or fail-fast behavior. Optional dependencies must not make core readiness fail.
External-provider failure must degrade features rather than trigger unbounded retries or cascade
failure.

## Database and network resilience

The production database remains multi-AZ with bounded connection pools, query timeouts, and
bounded retry behavior during failover. Ingress spans multiple AZs and removes unhealthy targets.
No critical production dependency may rely on a single AZ.

## Graceful degradation

- Premium provider failure disables Premium actions without taking down core service.
- Notification provider failure queues or drops safely according to bounded policy.
- AI provider failure disables AI features.
- Location-provider failure preserves non-location features.
- Optional-feature failures must preserve the core read path where possible.

## Resource bounds

Production must enforce request-body/upload limits, worker concurrency limits, background-job
retry limits, and bounded cache TTLs. These controls prevent overload from turning into
unbounded memory, queue, or retry growth.

## Evidence boundary

D07 adds deterministic policy validation only. It does not claim live load, database failover,
AZ-failure, or dependency-chaos evidence. Those remain explicit live production-readiness tests.

The machine-readable contract is
`infrastructure/environments/production/resilience-contract.json`, validated by
`scripts/ci/check-production-resilience.py`.
