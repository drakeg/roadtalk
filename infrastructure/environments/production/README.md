# Production Terraform root

Sprint 15 production work is contract-gated. This directory remains non-deploying through S15-D04.

Machine-readable production contracts:

- `production-contract.json` — environment, topology, TLS, immutable artifact, release, and rollback boundaries.
- `identity-contract.json` — CI/CD identity, least privilege, managed secrets, rotation, human access, and break-glass boundaries.
- `observability-contract.json` — health/readiness, structured logging, metrics, alerting, SLO/error-budget, privacy, and release-health boundaries.

CI validates these contracts with:

- `scripts/ci/check-production-contract.py`
- `scripts/ci/check-production-identity.py`
- `scripts/ci/check-production-observability.py`

Production telemetry must remain privacy-bounded: no secret values, raw authorization/cookie
headers, payment data, precise location, unrelated-user payloads, or user-specific metric
labels. Health endpoints are non-sensitive and release health gates fail closed.

D02-D04 do **not** create production Terraform resources, IAM/OIDC resources, monitoring
services, DNS records, certificates, provider credentials, or recurring spend. Production
traffic and live evidence remain separately gated by later Sprint 15 work.

Do not copy the single-host field-test topology into production.
