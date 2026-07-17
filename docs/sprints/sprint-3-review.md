# Sprint 3 review record

- Sprint: 3 — Location
- Status: Approved upon merge of this review
- Review date: 2026-07-16
- Deliverable: S03-D09
- Issue: #80
- Acceptance: S03-T12

## Decision requested

Merging this review records product-owner approval of the completed Sprint 3
repository/CI scope and authorizes Sprint 4 planning. It does not authorize a field
test, close Sprint 1 exceptions, enable AWS resources, or claim unperformed physical-
device or operational evidence.

## Review outcome

S03-D01 through S03-D08 are complete and merged. The implementation provides explicit
foreground consent, one short-lived current PostGIS row, validated GPS/heading/speed
samples, owner-local sensor quality, and privacy-preserving coarse nearby awareness.
The database, API, mobile lifecycle/experience, privacy/security gates, prior-sprint
regressions, and operator documentation were reviewed against the approved
specification.

All repository/CI acceptance evidence is green. The product-owner decision becomes
**APPROVED** when this review pull request is merged. Tracker #81 may then close and
Sprint 4 planning may begin under a separately approved specification/readiness gate.

## Demonstration record

Demonstrated with synthetic data through CI and repository review:

- purpose-before-permission and precise/approximate/denied/blocked/unavailable states
- versioned foreground consent grant, replay, replacement, and withdrawal
- one indexed current PostGIS row with replacement, expiry, cleanup, and cascades
- coordinate, accuracy, time, heading, speed, sequence, source, race, and plausible-
  movement validation with stable non-disclosing failures
- owner-scoped consent/location mutation and semantic nearby API contracts
- indexed empty/self/boundary/stale/inaccurate/degraded/withdrawn nearby fixtures
- owner-only accuracy, heading, speed, unavailable, and stale mobile states
- none/few/many nearby UI with bounded foreground polling and safe retry/expiry
- sampling/polling/timer/state stops on pause, background, screen exit, logout,
  native failure, and unmount
- multidimensional limits, exact OpenAPI, closed logs, dependency/permission gates,
  and synthetic leakage injection
- full Sprint 1/2 backend, PostGIS/migration, mobile, dependency, container, and
  zero-resource Terraform regression suite

The detailed mapping is in
[Sprint 3 synthetic foreground-location evidence](../evidence/sprint-3/README.md).

Not demonstrated and not claimed:

- installed iOS or Android development builds on physical devices
- real permission dialogs, GPS behavior, battery use, or native storage inspection
- clean-machine end-to-end setup
- an enabled AWS plan or deployed field-test environment
- backup/restore, alarm, budget, or operational AWS rehearsal
- production/multi-worker shared rate limiting or anti-spoof guarantees

## Acceptance results

| Test group | Result | Review evidence |
|---|---|---|
| S03-T01–T05 persistence, policy, API, nearby | PASS | Live PostGIS migration/lifecycle, quality, boundary, and query-plan tests |
| S03-T06 contracts/privacy | PASS | Authentication, exact schemas, stable problems, limits, and leakage tests |
| S03-T07 permission flow | PASS — automated | Purpose/permission/error/accessibility tests; device evidence pending |
| S03-T08 lifecycle/UX | PASS — automated | Fake-clock sampling, sensor state, nearby polling, retry, stop, and stale tests; device evidence pending |
| S03-T09 mobile scope | PASS | Configuration, dependency, storage, URL, log, semantic UI, and forbidden-feature gates |
| S03-T10 leakage | PASS | Synthetic markers, closed logs, exact OpenAPI, and privacy/scope CI gates |
| S03-T11 regressions | PASS | Backend/PostGIS/migration, mobile, security, container, and Terraform jobs |
| S03-T12 review | APPROVED UPON MERGE | Traceability, synthetic evidence, cost/privacy review, limitations, retrospective, and decision |

See [Sprint 3 traceability and evidence](sprint-3-traceability.md) for the complete
requirement-to-test-to-deliverable mapping.

## Definition of Done

- [x] S03-R01 through S03-R12 implemented and traced
- [x] S03-T01 through S03-T11 pass within the repository/CI evidence boundary
- [x] S03-D01 through S03-D08 complete and merged
- [x] backend/PostGIS/migrations, mobile, security, container, and IaC gates pass
- [x] foreground location and coarse nearby lifecycle demonstrated synthetically
- [x] no coordinate, movement, candidate identity, exact count/distance/bearing,
  location history, background task/permission, map, analytics, or later-sprint scope
  enters public output, logs, storage, or evidence
- [x] no AWS resource or incremental recurring cost introduced
- [x] activation projection, limitations, and evidence boundaries recorded
- [ ] S03-D09 review merged and S03-T12 product-owner approval effective
- [ ] Sprint 3 tracker closed as completed

The final two boxes are completed operationally after this review is merged and must
not be represented as complete beforehand.

## Cost decision

**Approved incremental AWS cost: $0/month.** Terraform remains disabled and current
RoadTalk AWS cost remains $0. No RDS, Redis, NAT Gateway, ALB, Fargate, Lambda,
scheduler, map/geocoder, analytics provider, or extra compute was introduced.

If the existing field-test stack is later enabled continuously, budget **$20–$23 per
month without the temporary compute promotion** or approximately **$8–$11 while an
applicable promotion remains available**, before tax and heavy traffic. Use a **$30
monthly planning budget** rather than relying on the current $20 threshold. Enabling
the environment remains a separate product-owner and Sprint 1 exception decision.

## Known limitations and accepted design boundaries

- Consumer GPS is not cryptographic; spoofing remains possible despite freshness,
  accuracy, sequencing, source, plausible-movement, and rate controls.
- Repeated semantic nearby queries may reveal approximate presence. Coarse buckets,
  caller-location requirements, expiry, and limits reduce but do not eliminate this.
- Heading, speed, and accuracy are non-authoritative device observations and may be
  absent, delayed, or wrong. RoadTalk makes no navigation, driving, emergency, or
  safety guarantee.
- Location and nearby limiters are process-local for the approved single-worker
  field-test design. Multi-worker scaling requires a shared-control architecture and
  cost decision supported by measurements.
- Cleanup is not scheduled; expiry makes rows ineligible immediately and idempotent
  physical cleanup may occur opportunistically.
- Physical-device permissions, battery, GPS, accessibility, native storage, and OS
  lifecycle behavior remain unverified.
- S01-E01 through S01-E03 remain hard blockers for any field test.
- Background location, maps, routes, location history, exact nearby details, audio,
  PTT, channels, and all Sprint 4+ behavior remain out of scope.

## Retrospective

What worked:

- privacy and expiry designed before location collection or public contracts
- one-row persistence and semantic output prevented history and identity scope growth
- PostGIS boundary/query-plan evidence kept nearby evaluation correct and measurable
- fake-clock mobile tests covered every lifecycle stop without claiming device proof
- exact OpenAPI, dependency, permission, logging, and Terraform gates failed closed
- no map/geocoder, analytics, cache, scheduler, or managed-service cost was introduced
- cost reporting now distinguishes disabled, incremental, activation, and monthly cost

Improvements:

- close physical-device evidence gates before relying on native behavior in a field test
- add a named cross-layer synthetic lifecycle earlier in future sprint implementation
- replace process-local limits only after measurements justify multi-worker deployment
- revise the Terraform budget threshold before enabling the field-test stack
- evaluate Sprint 4 media usage/cost independently before selecting or enabling any
  LiveKit capacity or related AWS networking
- keep merge-bound approval language explicit so review evidence never claims a
  product-owner decision before merge

## Approval decision and next action

**Decision: approved upon merge.** Merging this review completes S03-D09 and S03-T12,
authorizes closing issue #80 and tracker #81, and permits Sprint 4 planning. It does
not authorize Sprint 4 coding before a separately approved specification/readiness
record, and it does not authorize a field test while S01-E01 through S01-E03 remain
open.
