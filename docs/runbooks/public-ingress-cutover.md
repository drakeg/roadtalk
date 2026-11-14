# Public ingress cutover and rollback runbook

Status: deterministic preflight only; live cutover requires separate S16-D02 authorization.

## Preconditions

- Valid, unexpired launch authorization explicitly includes DNS/traffic scope.
- Domain ownership and authoritative zone are verified.
- Production hostname and certificate hostname match.
- Certificate meets minimum validity and TLS requirements.
- Current DNS target is recorded as the rollback target.
- Exact release and rollback artifacts are known.
- Pre-cutover health is green.
- Incident owner and operator are named.

## Bounded cutover

1. Lower or confirm DNS TTL within the approved maximum before the change window.
2. Record current DNS values and change identifier.
3. Route no more than the approved initial traffic percentage.
4. Observe health, error rate, latency, saturation, and alert state for the required interval.
5. Increase traffic only through separately approved steps.
6. Stop immediately if health checks, error budget, security/privacy gates, or operator stop
   conditions fail.

## Rollback

Revert to the recorded previous DNS target, confirm the known-good rollback artifact if needed,
verify TLS and health, disable public ingress if recovery is uncertain, and record the evidence.

## Prohibited actions in D03

Do not change live DNS, request production certificates, expose databases/caches publicly, shift
real users, or incur new recurring infrastructure cost merely to validate this runbook.
