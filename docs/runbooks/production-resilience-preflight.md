# Load, failover, and degraded-mode preflight

Sprint 16 owner: S16-D07 / #482.

## Load-test bounds

Every load exercise must identify its environment and operator and must define bounded duration,
concurrency, request rate, error-rate abort threshold, p95 latency abort threshold, and cost guard.
Automatic production execution is prohibited.

## Failure scenarios

Before public beta, RoadTalk must have explicit profiles for database failover, AZ failure, cache
failure, external-provider failure, and network partition behavior.

Destructive failure injection is disabled by default. Production failure injection remains
unauthorized by D07 and requires separate explicit approval.

## Mandatory stop conditions

A test stops when health gates fail, the error budget is breached, a security/privacy signal
appears, the cost guard is exceeded, or the operator aborts.

## Graceful degradation

Optional-service failures must not take down the core read path. Premium, notification, AI, and
location integrations degrade safely according to the production resilience contract.

## Evidence boundary

D07 defines deterministic test profiles and safety controls only. It does not perform or claim live
production load testing, database/AZ failover, dependency chaos, or production failure injection.
