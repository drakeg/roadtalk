# Production observability and incident-readiness preflight

Sprint 16 owner: S16-D05 / #480.

## Health

Preflight requires separate liveness/readiness signals, database and cache readiness checks, and
a recorded preflight health result. Optional external dependencies must not block core readiness.

## SLO and error budget

Initial public-beta targets remain availability >=99.5%, p95 latency <=1000 ms, and server error
rate <=1%. The measurement window must be documented and an exhausted error budget blocks release.

## Alert delivery

Every production alert requires a delivery path, named owner, severity, runbook, deduplication,
and a pre-launch test notification. Alerts must not contain secrets or raw user payloads.

## Incident readiness

Before public beta, RoadTalk requires:
- a named incident owner;
- documented severity model;
- escalation path;
- status communication path;
- after-action review process;
- a production incident exercise.

The exercise requirement is recorded here, but D05 does not claim the live exercise has occurred.

## Telemetry privacy

Logs, metrics, and alerts must exclude authorization/cookie headers, secret values, payment data,
precise location, unrelated user payloads, user-ID labels, and unbounded metric cardinality.

## Release health gate

Any future release must pass pre/post health checks, observe for at least 10 minutes, and roll back
or halt on failed health. Automatic real-user rollout remains prohibited.

## Evidence boundary

D05 proves deterministic preflight requirements only. It does not claim live alert delivery,
measured SLOs, a live incident exercise, or a live release-health gate.

Source: `infrastructure/environments/production/observability-preflight-contract.json`  
Validator: `scripts/ci/check-observability-preflight.py`
