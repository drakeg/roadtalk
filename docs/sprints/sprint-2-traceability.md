# Sprint 2 traceability and evidence

- Sprint: 2 — Identity
- Status: Ready for product-owner approval
- Deliverable: S02-D10
- Issue: #60
- Implementation baseline: merge commit `1769e873262a3b932caaf3ff990923cd4325b199`
- Evidence date: 2026-07-14

## Status vocabulary

- **Passed — automated:** reproducible GitHub CI or repository tests passed.
- **Passed — inspection:** contracts, documentation, and scope guardrails were
  reviewed against the merged implementation.
- **Not performed — field:** requires a clean machine, installed mobile build, or
  enabled AWS field-test environment and is not represented as passed.
- **Approved upon merge:** merging the Sprint 2 review records the product-owner
  decision after all other evidence is green.

## Requirement traceability

| Requirement | Deliverable(s) | Test(s) | Evidence | Status |
|---|---|---|---|---|
| S02-R01 Profile persistence | D02 | T01, T11 | PR [#62](https://github.com/drakeg/roadtalk/pull/62); optional one-to-one profile migration/model and live PostgreSQL invariants | Passed — automated |
| S02-R02 Callsign policy | D03 | T02, T11 | PR [#63](https://github.com/drakeg/roadtalk/pull/63); normalization, reserved/confusable, collision, and policy corpus tests | Passed — automated |
| S02-R03 Callsign availability | D03 | T02, T08, T11 | PR #63; authenticated non-enumerating availability and limiter tests | Passed — automated |
| S02-R04 Private profile API | D04, D05 | T03, T11 | PRs [#64](https://github.com/drakeg/roadtalk/pull/64) and [#65](https://github.com/drakeg/roadtalk/pull/65); owner-only read/update, over-posting, conflict, cooldown, and database tests | Passed — automated |
| S02-R05 Public identity contract | D04 | T03, T10 | PR #64; exact DTO and OpenAPI allowlist limited to callsign and bundled-avatar ID | Passed — automated and inspection |
| S02-R06 Bundled avatar catalog | D05 | T04, T11 | PR #65; backend/mobile catalog comparison, active/retired/unknown behavior, and accessibility tests | Passed — automated |
| S02-R07 Identity mobile experience | D06 | T05, T11 | PR [#66](https://github.com/drakeg/roadtalk/pull/66); setup/settings, invalid/unavailable/conflict/offline/retry, and accessibility tests | Passed — automated |
| S02-R08 Optional anonymous recovery | D07, D08 | T06, T11 | PRs [#67](https://github.com/drakeg/roadtalk/pull/67) and [#68](https://github.com/drakeg/roadtalk/pull/68); key creation, transfer, rotation, session replacement, and one-time UI tests | Passed — automated |
| S02-R09 Recovery containment | D07–D09 | T06–T08, T10, T11 | PRs #67–[#69](https://github.com/drakeg/roadtalk/pull/69); replay/revocation, constant-shape errors, leakage, storage, URL, and limiter tests | Passed — automated and inspection |
| S02-R10 Identity privacy and abuse | D03–D09 | T02, T07, T08, T10 | enumeration tests, reserved names, closed-field logs, route templates, rate limits, and privacy gate | Passed — automated and inspection |
| S02-R11 Compatibility and migration | D02–D09 | T01, T09 | empty/previous database migration, drift, downgrade/forward, Sprint 1 auth regression, container, and zero-resource Terraform gates | Passed — automated |
| S02-R12 Quality and evidence | D01, D09, D10 | T10–T12 | approved specification/readiness, PR #69 hardening/runbooks, this traceability and review package | Approved upon review merge |

## Acceptance-test evidence

| Test | Evidence | Result |
|---|---|---|
| S02-T01 persistence migration | Empty and prior-schema upgrades, constraints, drift, downgrade/forward, and live PostgreSQL profile tests | PASS — automated |
| S02-T02 callsign policy/availability | Shared normalization corpus, invalid/reserved/confusable inputs, collisions, owner-free responses, and limiter tests | PASS — automated |
| S02-T03 profile authorization/concurrency | Owner-only routes, missing authentication, over-posting, stale-version, cooldown, and lifecycle tests | PASS — automated |
| S02-T04 avatar catalog | Backend/mobile metadata equality, accessible rendering, retained retired values, and unknown/retired rejection | PASS — automated |
| S02-T05 mobile identity | Setup/settings, local validation, unavailable, offline retry, optimistic conflict, accessibility, and scope tests | PASS — automated |
| S02-T06 recovery lifecycle | Synthetic key creation, second-device transfer, rotation, replay rejection, and old-session revocation | PASS — automated |
| S02-T07 recovery privacy | Invalid/unknown/replayed HTTP shape equality, URL/storage/UI constraints, and log leakage injection | PASS — automated |
| S02-T08 abuse limits | Availability, mutation, peer, installation, selector, account, and device dimensions return stable bounded 429 responses | PASS — automated |
| S02-T09 Sprint 1 regression | Backend/PostGIS/migrations, mobile, dependencies, secrets, container, and zero-resource Terraform jobs | PASS — automated |
| S02-T10 contracts/scope | Exact OpenAPI schemas, backend/mobile catalog agreement, dependency/permission/privacy allowlists, and later-sprint exclusions | PASS — automated and inspection |
| S02-T11 identity demonstration | Composed synthetic registration, setup, conflict, avatar, recovery transfer, settings, session replacement, replay, and revocation evidence in `docs/evidence/sprint-2/README.md` | PASS — automated synthetic evidence; no field claim |
| S02-T12 sprint review | Traceability, documentation, cost/privacy audit, limitations, retrospective, and merge-bound product-owner decision | APPROVED UPON REVIEW MERGE |

## Automated baseline

[CI run 29381798557](https://github.com/drakeg/roadtalk/actions/runs/29381798557)
validated the D09 head `9e17491094780ab32df7f5157b7927a16789c712`
before merge. All required jobs passed:

- Backend, database, and migrations
- Mobile quality
- Dependencies, secrets, containers, and IaC

The run includes full PostgreSQL tests and coverage, migration lifecycle checks,
Expo Doctor, TypeScript, Jest, dependency audits, the Sprint 2 privacy/scope gate,
Terraform validation and zero-resource guards, container build, and security scans.
The D10 review pull request must pass the same gates before merge.

## Deliverable audit

| Deliverable | Issue | Pull request/evidence | State |
|---|---:|---|---|
| S02-D01 | #51 | PR [#50](https://github.com/drakeg/roadtalk/pull/50), readiness, and tracker #61 | Complete |
| S02-D02 | #52 | PR #62 | Merged |
| S02-D03 | #53 | PR #63 | Merged |
| S02-D04 | #54 | PR #64 | Merged |
| S02-D05 | #57 | PR #65 | Merged |
| S02-D06 | #55 | PR #66 | Merged |
| S02-D07 | #59 | PR #67 | Merged |
| S02-D08 | #56 | PR #68 | Merged |
| S02-D09 | #58 | PR #69 | Merged |
| S02-D10 | #60 | Traceability, evidence, and review package | Approved upon merge |

## Privacy and scope audit

Repository contracts expose only the approved identity, avatar, and recovery
surfaces. Public identity remains callsign plus catalog avatar identifier. Recovery
material is returned only during creation or successful rotation, stored server-side
only as a salted and peppered slow hash, excluded from URLs and logs, and written to
device SecureStore only after explicit opt-in. Logs accept only closed event/field
allowlists and route templates.

The mobile configuration and dependencies add no location, microphone, contacts,
photos, notification, tracking, uploaded-media, clipboard, or analytics capability.
No channel, nearby, map, moderation, subscription, or other later-sprint feature was
introduced.

## Cost audit

Sprint 2 created no AWS resource. Terraform remains disabled by default and CI uses
no AWS credentials. The implementation reuses the existing API and PostgreSQL design
and bundles avatar assets with the application. No RDS, NAT Gateway, managed Redis,
ALB, Fargate, Cognito, SES, SNS, Pinpoint, Lambda, S3, CloudFront, or image service
was added. Expected incremental AWS cost remains **$0**.

## Evidence boundary

No clean-machine, installed-device, enabled Terraform, deployed field-test,
backup/restore, alarm, or AWS cost rehearsal was performed for this record. Sprint 1
exceptions S01-E01 through S01-E03 remain open and continue to block field testing.
This Sprint 2 evidence demonstrates repository and CI behavior only.
