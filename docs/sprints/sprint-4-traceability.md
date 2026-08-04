# Sprint 4 traceability and evidence

- Sprint: 4 — Push-to-Talk
- Status: Ready for product-owner approval
- Deliverable: S04-D09
- Issue: #99
- Implementation baseline: merge commit `1ce65eced0a1be4bab40279c0b652b3a9ef9d0d5`
- Evidence date: 2026-08-04

## Status vocabulary

- **Passed — automated:** reproducible repository or GitHub CI checks passed.
- **Passed — inspection:** contracts, documentation, privacy, cost, and scope controls
  were reviewed against the merged implementation.
- **Not performed — field:** requires physical devices, a live provider, or enabled
  AWS and is not represented as passed.
- **Approved upon merge:** merging the Sprint 4 review records the product-owner
  decision after the review pull request is green.

## Requirement traceability

| Requirement | Deliverable(s) | Test(s) | Evidence | Status |
|---|---|---|---|---|
| S04-R01 Provider boundary | D02, D07 | T01, T09 | PRs [#101](https://github.com/drakeg/roadtalk/pull/101), [#106](https://github.com/drakeg/roadtalk/pull/106); typed provider contract, disabled factory, deterministic fake, failure tests | Passed — automated and inspection |
| S04-R02 Metadata-only grants | D02–D04, D07 | T02, T09 | PRs #101–#103 and #106; migrations, constraints, expiry/revocation, deletion, schema/log gates | Passed — automated |
| S04-R03 Receive authorization | D03, D07 | T03, T09 | PR [#102](https://github.com/drakeg/roadtalk/pull/102); authenticated idempotent receive API and synthetic claim tests | Passed — automated |
| S04-R04 Transmit authorization | D04, D07 | T04, T05 | PRs [#103](https://github.com/drakeg/roadtalk/pull/103) and #106; ownership, microphone-only scope, concurrency, degraded-state denial | Passed — automated |
| S04-R05 Release and expiry | D03, D04, D07 | T05, T10 | release, expiry, session/device/account invalidation, ambiguous-failure, and bounded reconciliation tests | Passed — automated |
| S04-R06 Microphone consent/lifecycle | D05–D07 | T06, T08 | PRs [#104](https://github.com/drakeg/roadtalk/pull/104)–#106; purpose-first permission and deterministic stop paths | Passed — automated; field evidence pending |
| S04-R07 Receive-ready media | D05–D07 | T07, T10 | fake room/audio adapter, join-with-capture-off, remote events, reconnect and lifecycle cleanup tests | Passed — automated; live/device evidence pending |
| S04-R08 Hold-to-talk state machine | D06, D07 | T08, T10 | PRs [#105](https://github.com/drakeg/roadtalk/pull/105) and #106; fake-clock authorization/capture ordering, 30-second stop, accessibility states | Passed — automated; field evidence pending |
| S04-R09 Media privacy/security | D02–D07 | T09 | exact OpenAPI, provider claims, dependencies, native configuration, database/log/evidence gates | Passed — automated and inspection |
| S04-R10 Reliability/evidence | D03–D09 | T10, T12 | failure/reconnect/revocation suites, synthetic scale test, evidence corpus, final review | Passed upon green review CI; media NFRs pending field evidence |
| S04-R11 Cost controls | D01, D05–D09 | T11 | PR [#107](https://github.com/drakeg/roadtalk/pull/107); disabled Terraform, $10 cap, usage stops, activation/destroy runbook | Passed — automated and inspection |
| S04-R12 Compatibility/scope | D01–D09 | T09–T12 | full Sprint 1–3 regressions and exact privacy/scope gates | Approved upon review merge |

## Acceptance-test evidence

| Test | Evidence | Result |
|---|---|---|
| S04-T01 provider contract | Synthetic credential/permission/removal shapes, injected failures, disabled configuration/factory | PASS — automated |
| S04-T02 metadata lifecycle | Empty/prior migrations, constraints, expiry/revocation, cascade deletion, drift and downgrade/forward | PASS — automated |
| S04-T03 receive authorization | Auth, idempotency/replay/conflict, rate, over-posting, one-time token and deny-all-publish claims | PASS — automated |
| S04-T04 transmit authorization | Ownership, expiry, cross-device, busy, degraded, duplicate and microphone-only promotion | PASS — automated |
| S04-T05 release/failure | Release/expiry/session/device/account invalidation, timeout/partial failure and reconciliation | PASS — automated |
| S04-T06 microphone permission | Unasked, purpose-first, granted, denied, blocked/settings, unavailable, retry and lifecycle transitions | PASS — automated; physical device not performed |
| S04-T07 receive-ready media | Fake adapter join/receive/reconnect/background/exit/logout/unmount with capture disabled | PASS — automated; live provider not performed |
| S04-T08 hold-to-talk | Fake-clock press/release/races/timeout/incoming/busy/error/accessibility and mandatory stops | PASS — automated; physical device not performed |
| S04-T09 security/privacy | OpenAPI, claims, dependency/config, native permission, storage/log/database/evidence and scope gates | PASS — automated and inspection |
| S04-T10 reliability/scale | Full regression suites plus 100 synthetic accounts, 25 connected receivers, 10 publishers, eligible and denied grant p95 ≤250 ms | PASS upon green review CI; live media NFRs not performed |
| S04-T11 zero-cost IaC | Disabled zero-resource Terraform, TFLint/Trivy, forbidden-service scan, $10 budget and operator stops | PASS — automated and inspection |
| S04-T12 demonstration/review | Synthetic lifecycle, traceability, privacy/security/cost/risk review, limitations and retrospective | APPROVED UPON REVIEW MERGE |

## Automated baseline

[CI run 30872234717](https://github.com/drakeg/roadtalk/actions/runs/30872234717)
validated the final D08 evidence commit `705da42f3b87c5d3702dc3e5bd73f233c8d5082a`.
Backend/PostGIS/migrations, mobile, dependency audits, privacy/scope gates, Terraform,
TFLint, Trivy, container build/scan, and artifact reporting all passed. The D09 review
pull request must pass those same jobs plus the synthetic scale measurement.

## Deliverable audit

| Deliverable | Issue | Pull request/evidence | State |
|---|---:|---|---|
| S04-D01 | #91 | Approved specification/readiness and tracker #100 | Complete |
| S04-D02 | #92 | PR #101 | Merged |
| S04-D03 | #93 | PR #102 | Merged |
| S04-D04 | #94 | PR #103 | Merged |
| S04-D05 | #95 | PR #104 | Merged |
| S04-D06 | #96 | PR #105 | Merged |
| S04-D07 | #97 | PR #106 | Merged |
| S04-D08 | #98 | PR #107 | Merged |
| S04-D09 | #99 | Traceability, scale evidence, and review package | Approved upon merge |

## Privacy, security, and scope audit

RoadTalk persists opaque, short-lived grant metadata only. It never persists signed
participant tokens, provider secrets, audio, transcripts, callsigns, coordinates, or
listener membership. The API derives ownership, room, participant, permission, policy,
and TTL server-side. Receive authority cannot publish; transmit authority is nested,
short-lived, and microphone-only. Local authorization is revoked before provider
cleanup on uncertain paths.

Mobile requests microphone permission only after explanation and explicit action,
joins receive-ready with capture off, and enables capture only after server/provider
authorization. Release, timeout, background, screen exit, logout/revocation,
reconnect, failure, and unmount stop capture before cleanup. No background audio,
camera, screen share, remote unmute, hands-free mode, recording, egress,
transcription, telephony, AI, proximity, channels, maps, or later-sprint behavior is
approved.

## Cost audit and activation projection

Sprint 4 created no AWS or LiveKit resource, credential, project, payment method, or
provider call. Terraform remains disabled and plans zero resources. Current and
incremental recurring cost is **$0/month**.

| Future posture | Projected monthly cost | Decision |
|---|---:|---|
| Local and GitHub CI | **$0** | Current |
| Separately approved device test using LiveKit Build with local backend | **$0** within RoadTalk stops | Not activated |
| Separately approved scheduled AWS window, then destroyed | **about $4–$6 in an active test month** | Not activated |
| Fully destroyed inactive month | **$0** | Required default |
| Intentionally retained storage/backups | **about $3–$5** | Separate retention decision |
| Always-on AWS or paid LiveKit | **Prohibited** | New dated architecture/cost approval required |

Hard controlled-test stops remain 3,000 participant-minutes, 10 GB downstream, 25
concurrent participants, and $10 total incremental monthly cost. Budgets and provider
quotas notify; they do not shut down resources automatically or authorize continued
spend.

## Evidence boundary

No physical-device microphone, audio-route, Bluetooth, interruption, accessibility
gesture, battery, data-use, press-to-audible latency, jitter/loss, cellular/Wi-Fi,
NAT/TURN, real provider revocation, enabled AWS plan, deployment, destroy, billing, or
automatic-shutdown evidence was performed. S01-E01 through S01-E03 remain open and
block field testing. Synthetic grant p95 does not prove media latency or physical
capacity.
