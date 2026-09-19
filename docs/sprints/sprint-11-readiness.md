# Sprint 11 readiness: Convoys

- Planning date: 2026-09-19
- Planning issue: #283
- Implementation tracker: #284
- Proposed baseline: Sprints 0–10 accepted; corrective browser/admin backlog #208 completed.

## Decision

**READY FOR PRODUCT-OWNER REVIEW; IMPLEMENTATION NOT YET AUTHORIZED.**

Sprint 11 implementation may begin only after the planning PR containing this readiness record and `sprint-11-convoys.md` is merged.

## Entry criteria

- Sprint 10 D10 is accepted and post-Sprint-10 corrective work is complete.
- Sprint roadmap identifies Sprint 11 as Convoys.
- S11-R01–R12 and S11-T01–T12 are defined before implementation.
- D01–D10 and strict D02→D10 dependency order are locked in tracker #284.
- Incremental recurring implementation cost is $0.
- Existing account/session/location/proximity/Same-road/channel/media authorization remains authoritative.

## Privacy and authorization readiness

1. convoy membership cannot broaden upstream authorization;
2. no raw/durable location or route history;
3. no background location/audio;
4. no unrelated-user presence or cross-convoy enumeration;
5. current convoy awareness derives only from already-authorized current state and expires/fails closed with it;
6. stale/revoked/left/disbanded membership fails closed;
7. no private credentials, recovery material, provider secrets, implicit recipient override or provider bypass enters convoy payloads/logs/evidence.

## Provider and cost readiness

D02–D10 require no external provider. Local Docker/PostgreSQL/PostGIS and GitHub CI are sufficient. No AWS/LiveKit Cloud, map/location/messaging provider account, API key, network activation, payment method or recurring-spend service is authorized.

## Delivery readiness

Locked order after D01 merge: #274, #275, #276, #277, #278, #279, #280, #281, #282. Only one implementation deliverable should advance at a time unless a future explicit product-owner decision changes the plan.

## Verification plan

Contract/over-posting tests; membership lifecycle/concurrency/revocation tests; authorization-composition regressions; current-awareness staleness/consent tests; privacy/enumeration/log gates; browser/mobile accessibility and degraded-state tests; deterministic scale/compatibility evidence with targets locked before the named run; full backend/mobile/security/migration/schema-drift/Compose/IaC gates.

## Named evidence exceptions

Not Sprint 11 acceptance evidence unless separately performed later: physical-device convoy behavior; suspended/killed/background execution; roaming/network transitions; real-world GPS boundary/heading accuracy; external-provider latency/quota/privacy/terms/cost; production/public-beta capacity/failover; AWS deployment/billing/destroy; or background location/audio behavior.

## Approval effect

Product-owner merge of the Sprint 11 planning PR approves only the locked $0 local/GitHub-CI D02→D10 sequence and these boundaries. Sprint 11 acceptance occurs only at D10. Sprint 12 requires separate planning/readiness approval.
