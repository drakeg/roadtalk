# Sprint 10 readiness: Campgrounds

- Planning date: 2026-09-06
- Planning issue: #255
- Implementation tracker: #256
- Proposed baseline: Sprint 9 accepted; local-LAN follow-up PR #245 merged.

## Decision

**READY FOR PRODUCT-OWNER REVIEW; IMPLEMENTATION NOT YET AUTHORIZED.**

Sprint 10 implementation may begin only after the planning PR containing this readiness record and `sprint-10-campgrounds.md` is merged.

## Entry criteria

- Sprint 9 D10 acceptance is merged and the post-sprint local-LAN Docker fix is merged.
- Sprint roadmap identifies Sprint 10 as Campgrounds.
- S10-R01–R12 and S10-T01–T12 are defined before implementation.
- D01–D10 and strict D02→D10 dependency order are locked in tracker #256.
- Current/incremental recurring implementation cost is $0.
- Existing account/session/location/proximity/channel/route/media/notification authorization remains authoritative.

## Privacy and authorization readiness

The implementation is ready only under these invariants:

1. campground context cannot broaden any upstream authorization;
2. no campsite/lot/unit-level user presence is exposed or persisted;
3. no exact campground occupancy/member list/count or person-at-campground enumeration;
4. no durable visit, arrival/departure or campground-derived movement history;
5. current context is server-derived from already-authorized current state and expires/fails closed with that state;
6. no background location/audio is introduced;
7. no private username/password/recovery/authentication secret, recipient override or provider credential enters campground payloads/logs/evidence.

## Data/provider readiness

Sprint 10 local/CI acceptance uses deterministic catalog data only. No external campground, place, map or reservation provider is selected or approved. No provider account, API key, network call, scraping, payment method, booking inventory or transaction flow is required for D02–D10.

Any later real data-source proposal must separately document licensing/attribution, permitted caching/storage, freshness/completeness semantics, privacy, quota/rate limits, operational dependency and recurring cost before activation.

## Delivery readiness

Locked order after D01 merge:

1. #246 — domain/privacy contract
2. #247 — persistence/deterministic catalog
3. #248 — current campground context/presence composition
4. #249 — channel/communication composition
5. #250 — browser UX
6. #251 — mobile UX
7. #252 — reliability/privacy hardening
8. #253 — scale/provider/compatibility evidence
9. #254 — final evidence/review

Only one implementation deliverable should advance at a time unless a future explicit product-owner decision changes the plan.

## Verification plan

- schema/over-posting and sensitive-field rejection;
- migration/persistence/deletion/provenance tests;
- deterministic search/filter/detail tests with zero external calls;
- current-context derivation, staleness, consent/revocation/deletion tests;
- authorization-composition regressions across proximity/channel/Same-road/media/notifications;
- browser/mobile accessibility and degraded-state tests;
- privacy/enumeration/log/dependency/provider gates;
- synthetic 100-account / 25 current-context / 10 publisher matrix plus representative campground catalog with p95 targets locked before the named run;
- full existing backend/mobile/security/Compose/IaC regression gates.

## Named blockers and evidence exceptions

These are explicitly **not** Sprint 10 acceptance evidence unless separately performed later: real campground/place/reservation data freshness/completeness/licensing, physical-device campground-boundary accuracy, suspended/killed/offline/roaming/network-transition behavior, external-provider latency/quota/privacy/terms/cost, production/public-beta capacity/failover, AWS deployment/billing/destroy, background location/audio, or booking/reservation/payment correctness.

## Cost and activation gate

Authorized planning/implementation ceiling after merge: **$0 incremental recurring cost** using existing local Docker/PostGIS and GitHub CI.

Not authorized: AWS/LiveKit Cloud activation, external campground/place/map/reservation providers, payment methods, paid/free-tier services with recurring-spend exposure, scraping, production/public beta, background tracking/audio, booking/payment integration or Sprint 11 implementation.

## Approval effect

Product-owner merge of the Sprint 10 planning PR approves only the locked local/GitHub-CI D02→D10 sequence and these boundaries. Sprint 10 acceptance occurs only at D10. Sprint 11 requires separate planning/readiness approval.