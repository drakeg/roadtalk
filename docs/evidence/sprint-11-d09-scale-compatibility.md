# Sprint 11 D09 scale and compatibility evidence

## Locked deterministic evidence profile

D09 uses only local/CI synthetic state. No external provider, cloud resource, production traffic or paid service is authorized.

Representative synthetic workload:
- 100 convoys
- 20 active members per convoy (2,000 memberships)
- one active foreground session/current-location record per synthetic active member
- existing channel/proximity/Same-road authorization remains authoritative

Locked targets for a local PostgreSQL/PostGIS evidence run:
- current convoy status lookup: p95 <= 100 ms
- current convoy awareness lookup for a 20-member convoy: p95 <= 250 ms
- create/join/leave lifecycle operation: p95 <= 250 ms

These targets are evidence thresholds, not production SLOs. Physical-device, roaming/network, real-GPS, external-provider latency/quota/privacy/terms/cost, production capacity/failover, AWS billing/destroy, and background execution remain named evidence exceptions.

## Compatibility/degraded-state matrix

| Condition | Required behavior |
| --- | --- |
| authenticated + active membership + current authorized state | bounded convoy status/awareness |
| no membership / left / revoked / expired | no convoy awareness; fail closed |
| disbanded convoy | no current convoy awareness |
| stale/denied location state | no stale member awareness |
| revoked/expired source session | member omitted from awareness |
| upstream channel/proximity/Same-road/media denial | convoy cannot restore eligibility |
| offline/client fetch failure | client must not infer or retain stale awareness |
| concurrent second active membership | database rejects it |
| external providers unavailable | convoy core remains deterministic; no provider dependency |

## Cost/provider evidence

The convoy implementation uses existing application/PostgreSQL/PostGIS state and deterministic browser/mobile clients. It introduces no Terraform resources, AWS/LiveKit Cloud activation, external map/location/messaging API, background collection, analytics service, or recurring-spend dependency. Incremental recurring implementation cost remains $0.

## Reproducibility

Repository-wide coding/validation standards are in `CONTRIBUTING.md`. CI parity is documented in `docs/runbooks/ci-quality-security.md`. The repaired `make pre-pr-check` target includes compile, formatting, lint, mypy and backend tests; migration changes additionally require migrate + drift checks.

Actual named performance measurements must be recorded only when executed in an environment capable of running the repository and PostgreSQL/PostGIS stack; this document does not fabricate unexecuted timings.
