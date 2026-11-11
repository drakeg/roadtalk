# Production resilience readiness runbook

Status: deterministic contract only; no live failure injection is authorized by S15-D07.

## Pre-launch validation categories

Future live readiness evidence must cover:

1. Sustained load at the approved target plus capacity headroom.
2. Burst traffic and rate-limit behavior.
3. Database failover with bounded application retry behavior.
4. Loss of one application availability zone.
5. Cache unavailability and recovery.
6. Optional provider timeouts/failures without core-service collapse.
7. Queue/backlog saturation and bounded recovery.
8. Resource exhaustion signals without uncontrolled retry amplification.

## Pass criteria

A future exercise must record request/error/latency behavior, saturation, retry counts, queue
depth, health state, alert behavior, and recovery time. Core functionality must remain available
where the contract defines graceful degradation.

## Stop conditions

Testing must stop if it risks production data integrity, bypasses approved traffic gates, causes
unbounded spend, or requires destructive changes. Failure injection must use an explicitly
approved environment and operator.

## Evidence honesty

Synthetic/local tests may prove deterministic behavior but do not prove production capacity,
multi-AZ failover, or live provider resilience. Those claims require measured live evidence.
