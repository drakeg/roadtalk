# DNS, TLS, and public-ingress cutover readiness

Sprint 16 owner: S16-D03 / #478.

## DNS readiness

Before any live cutover, RoadTalk requires verified domain ownership, an authoritative DNS zone,
an explicit production hostname, a recorded DNS change ID, and a rollback target. The maximum
planned cutover TTL is 300 seconds. This contract keeps DNS cutover authorization false.

## TLS readiness

Public ingress requires a valid certificate whose hostname matches the production hostname,
minimum TLS 1.2, HTTP-to-HTTPS redirect, and at least 14 days of remaining certificate lifetime
at the preflight checkpoint.

## Public ingress

Production ingress must use a managed multi-AZ load balancer with health checks and unhealthy
target removal. Database and cache services remain private.

## Cutover sequence

A future authorized cutover must:
1. pass pre-cutover health checks;
2. preserve the previous DNS target;
3. begin with a bounded traffic ramp of no more than 10%;
4. observe health for at least 10 minutes;
5. pass post-cutover health checks before increasing traffic;
6. revert DNS or disable ingress if health fails.

Automatic full cutover is prohibited.

## Evidence boundary

D03 proves deterministic preflight rules only. It does not perform DNS changes, certificate
validation against a live hostname, public ingress exercise, or real-user traffic shift.

Source: `infrastructure/environments/production/dns-tls-ingress-contract.json`  
Validator: `scripts/ci/check-dns-tls-ingress.py`
