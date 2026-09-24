# Sprint 12 readiness: Moderation

Status: **PROPOSED — implementation blocked until this planning baseline is merged.**

## Ready conditions

- Sprints 0–11 are accepted on `main`.
- S12-R01–R12 and S12-T01–T12 are defined before implementation.
- Delivery order is locked to #296 → #297 → #298 → #299 → #300 → #301 → #302 → #303 → #304.
- Moderation is restrictive only and cannot create communication eligibility.
- Reports are bounded metadata, not a channel for arbitrary sensitive evidence.
- Existing security/privacy/location/channel/convoy/media controls remain authoritative.
- Local Docker/PostgreSQL/PostGIS and GitHub CI are sufficient for authorized implementation.
- Incremental recurring implementation cost is $0; no external provider/cloud activation is authorized.

## Named evidence exceptions

Physical-device behavior; suspended/killed/background execution; roaming/network behavior; real GPS accuracy; external-provider latency/quota/privacy/terms/cost; production capacity/failover; AWS billing/destroy; background location/audio; real-world moderation staffing/response-time effectiveness.

## Approval effect

Merge of the D01 planning PR authorizes only D02→D10 in the locked order and boundaries above. It does not authorize Sprint 13 or any excluded provider/cloud/production/background capability.
