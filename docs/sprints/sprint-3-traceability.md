# Sprint 3 traceability and evidence

- Sprint: 3 — Location
- Status: Ready for product-owner approval
- Deliverable: S03-D09
- Issue: #80
- Implementation baseline: merge commit `f2e1823d4510321a21432544550738121d6ab668`
- Evidence date: 2026-07-16

## Status vocabulary

- **Passed — automated:** reproducible GitHub CI or repository tests passed.
- **Passed — inspection:** contracts, documentation, and scope guardrails were
  reviewed against the merged implementation.
- **Not performed — field:** requires installed mobile builds or an enabled AWS
  environment and is not represented as passed.
- **Approved upon merge:** merging the Sprint 3 review records the product-owner
  decision after all other repository/CI evidence is green.

## Requirement traceability

| Requirement | Deliverable(s) | Test(s) | Evidence | Status |
|---|---|---|---|---|
| S03-R01 Foreground consent | D02, D04 | T01, T02 | PRs [#82](https://github.com/drakeg/roadtalk/pull/82), [#84](https://github.com/drakeg/roadtalk/pull/84); append-only versioned consent, owner routes, replay/withdrawal tests | Passed — automated |
| S03-R02 Current-location persistence | D02 | T01, T04 | PR #82; one-row PostGIS model/migration, constraints, indexes, and cascade tests | Passed — automated |
| S03-R03 Location quality policy | D03 | T03, T04 | PR [#83](https://github.com/drakeg/roadtalk/pull/83); coordinate, accuracy, time, sequence, source, race, movement, quality, and expiry tests | Passed — automated |
| S03-R04 Private location API | D04 | T02, T03, T06 | PR #84; authenticated exact schemas, session-derived ownership, stable private errors, and metadata-only receipts | Passed — automated and inspection |
| S03-R05 Expiry and deletion | D02–D04, D08 | T02, T04, T06 | replacement, immediate ineligibility, pause/withdrawal, account/device cascade, and idempotent cleanup evidence | Passed — automated |
| S03-R06 Coarse nearby discovery | D05 | T05, T06 | PR [#85](https://github.com/drakeg/roadtalk/pull/85); indexed PostGIS boundary/query-plan fixtures and semantic-only output | Passed — automated |
| S03-R07 Foreground mobile permission | D06 | T07, T09 | PR [#86](https://github.com/drakeg/roadtalk/pull/86); purpose-before-permission, precise/approximate, denied, blocked, unavailable, retry, and accessibility tests | Passed — automated; field evidence pending |
| S03-R08 Foreground sampling | D06, D07 | T08, T09 | PRs #86 and [#87](https://github.com/drakeg/roadtalk/pull/87); bounded in-memory updates and deterministic lifecycle stops | Passed — automated; field evidence pending |
| S03-R09 Heading, speed, and nearby UX | D07 | T08, T09, T12 | PR #87; owner-only quality/freshness, unavailable/stale values, semantic buckets, and bounded polling tests | Passed — automated; field evidence pending |
| S03-R10 Privacy and abuse controls | D03–D05, D08 | T06, T09, T10 | PRs #83–#85 and [#88](https://github.com/drakeg/roadtalk/pull/88); multidimensional limits, exact contracts, closed logs, and location privacy/scope gate | Passed — automated and inspection |
| S03-R11 Compatibility and cost | D02–D08 | T01, T11 | full Sprint 1/2 regressions, PostGIS/migrations, mobile, dependency, container, and zero-resource Terraform gates | Passed — automated |
| S03-R12 Quality and evidence | D01, D08, D09 | T10–T12 | approved specification/readiness, PR #88 hardening/runbook, synthetic evidence, this traceability/review package | Approved upon review merge |

## Acceptance-test evidence

| Test | Evidence | Result |
|---|---|---|
| S03-T01 migration | Empty/prior-schema upgrades, constraints, indexes, drift, downgrade/forward, and live PostGIS model tests | PASS — automated |
| S03-T02 consent API | Grant/replay/replace/withdraw, missing auth, stale policy, over-posting, and atomic deletion tests | PASS — automated |
| S03-T03 quality policy | Boundary coordinates, accuracy, time, sequence, heading/speed, device races, and implausible movement tests | PASS — automated |
| S03-T04 current-row lifecycle | Replacement, expiry, pause, withdrawal, device/account cascade, and idempotent cleanup in migrated PostGIS | PASS — automated |
| S03-T05 nearby query | Empty/self, inside/outside radius, stale, inaccurate, degraded, withdrawn, semantic bucket, and GiST plan fixtures | PASS — automated |
| S03-T06 contracts/privacy | Authentication, exact OpenAPI, extra-field rejection, stable problems, bounded limits, and response/log leakage tests | PASS — automated and inspection |
| S03-T07 permission flow | Purpose-first, precise/approximate, denied, blocked/settings, unavailable, retry, and accessible UI states | PASS — automated; physical device not performed |
| S03-T08 mobile lifecycle | Fake location/AppState/navigation/logout clocks, dedupe, retry, pause, stale, polling, native failure, and unmount | PASS — automated; physical device not performed |
| S03-T09 mobile scope | Generated configuration, source/dependency/storage/log inspection, semantic UI, and forbidden-feature gate | PASS — automated and inspection |
| S03-T10 leakage corpus | Synthetic coordinate/movement/identity extras, exact schemas, closed logs, route templates, and CI privacy gates | PASS — automated |
| S03-T11 prior-sprint regression | Backend/PostGIS/migrations, mobile, dependency, secret, container, and disabled Terraform jobs | PASS — automated |
| S03-T12 demonstration/review | Composed synthetic lifecycle in `docs/evidence/sprint-3/README.md`; cost/privacy/limitations review | APPROVED UPON REVIEW MERGE |

## Automated baseline

[CI run 29546756307](https://github.com/drakeg/roadtalk/actions/runs/29546756307)
validated D08 head `56a36b7bbe42b43b731aa614987112104601d5f4` before
merge. All required jobs passed:

- Backend, database, and migrations
- Mobile quality
- Dependencies, secrets, containers, and IaC

The run includes live PostgreSQL/PostGIS tests and coverage, migration lifecycle,
Expo Doctor, TypeScript, Jest, dependency audits, identity and location privacy/scope
gates, Terraform validation and zero-resource guards, container build, and security
scans. The D09 review pull request must pass the same gates before merge.

## Deliverable audit

| Deliverable | Issue | Pull request/evidence | State |
|---|---:|---|---|
| S03-D01 | #72 | Approved specification/readiness and tracker #81 | Complete |
| S03-D02 | #73 | PR #82 | Merged |
| S03-D03 | #74 | PR #83 | Merged |
| S03-D04 | #75 | PR #84 | Merged |
| S03-D05 | #76 | PR #85 | Merged |
| S03-D06 | #77 | PR #86 | Merged |
| S03-D07 | #78 | PR #87 | Merged |
| S03-D08 | #79 | PR #88 | Merged |
| S03-D09 | #80 | Traceability, evidence, and review package | Approved upon merge |

## Privacy and scope audit

The server stores one short-lived current PostGIS row per account and separate
coordinate-free consent events. It exposes no coordinate read route. Location
acknowledgements contain metadata only, and nearby output is reduced to availability,
`none`/`few`/`many`, freshness, and the caller's expiry boundary before serialization.
Closed-field logs reject coordinates, accuracy, heading, speed, source identifiers,
callsigns, request bodies, and concrete paths.

Mobile requests only foreground/when-in-use location after an explicit explanation
and action. Coordinates remain in process memory and authenticated JSON requests;
subscriptions, polling, timers, and state stop on pause, background, screen exit,
logout, native failure, and unmount. There is no background task/permission, map,
geocoder, history, analytics, external location provider, nearby identity, exact
count/distance/bearing, WebSocket, PTT, channel, audio, or later-sprint behavior.

## Cost audit and activation projection

Sprint 3 created no AWS resource. Terraform remains disabled by default, so the
current AWS cost attributable to RoadTalk remains **$0**. Sprint 3 reuses the existing
API process and PostgreSQL/PostGIS design and adds no RDS, Redis, NAT Gateway, ALB,
Fargate, Lambda, scheduler, map/geocoder, analytics, or additional compute. Approved
incremental AWS cost is **$0/month**.

If the already-designed field-test stack is activated continuously in `us-east-1`,
the planning projection is:

| Activation period | Expected cost |
|---|---:|
| First 24 hours | $0.65–$0.80 |
| First 7 days | $4.50–$5.00 |
| Typical month during an applicable `t4g.small` promotion | $8–$11 |
| Typical month without the compute promotion | $20–$23 |
| Recommended monthly budget before activation | $30 |

These are planning estimates before tax and heavy traffic. The existing Terraform
`$20` notification threshold is too close to the recurring non-promotional floor and
should be raised or supplemented before activation. No environment is enabled by this
review.

## Evidence boundary

No physical-device permission prompt, native storage inspection, battery measurement,
clean-machine rehearsal, enabled Terraform plan, deployed field test, backup/restore,
alarm, budget, or AWS billing observation was performed for this record. S01-E01
through S01-E03 remain open and block field testing. Sprint 3 evidence demonstrates
repository and CI behavior with synthetic data only.
