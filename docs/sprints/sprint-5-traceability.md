# Sprint 5 traceability and evidence

- Sprint: 5 — Proximity Engine
- Status: Complete upon product-owner merge of the S05-D09 review
- Deliverable: S05-D09
- Issue: #118
- Implementation baseline: merge commit `d46041a655cdc10242fa6d620715c8ebf64ab7e2`
- Evidence date: 2026-08-14

## Status vocabulary

- **Passed — automated:** reproducible repository or GitHub CI checks passed.
- **Passed — inspection:** contracts, documentation, privacy, cost, and scope controls were reviewed.
- **Not performed — field:** requires physical devices, a live provider, or enabled AWS and is not represented as passed.
- **Approved upon merge:** merging the S05-D09 review records the product-owner decision.

## Requirement traceability

| Requirement | Deliverable(s) | Test(s) | Evidence | Status |
|---|---|---|---|---|
| S05-R01 Proximity policy | D01–D03, D08 | T01, T09 | approved policy/config, exact schemas, over-posting and planning/privacy gates | Passed — automated and inspection |
| S05-R02 Indexed eligibility | D02, D08 | T02, T10 | PR [#120](https://github.com/drakeg/roadtalk/pull/120); migrated PostGIS matrix, inclusive boundary, antimeridian/high-latitude and GiST-plan tests | Passed — automated |
| S05-R03 Sender authorization | D03, D05–D06 | T03, T06–T07 | PRs [#121](https://github.com/drakeg/roadtalk/pull/121), [#123](https://github.com/drakeg/roadtalk/pull/123), and [#124](https://github.com/drakeg/roadtalk/pull/124); ownership/location/audience/concurrency/failure tests | Passed — automated |
| S05-R04 Recipient authorization | D02–D03, D05–D06 | T04, T06–T07 | current account/device/session/location/consent/grant joins and recomputation tests; no membership persistence | Passed — automated |
| S05-R05 Selective subscription boundary | D04–D06 | T05–T07 | PR [#122](https://github.com/drakeg/roadtalk/pull/122); auto-subscribe false, verified track, exact subscribe/unsubscribe and deterministic failures | Passed — automated; live provider not performed |
| S05-R06 Publication handshake | D05, D08 | T06, T09 | PR #123; exact nested API, owned-microphone verification, replay/conflict, empty audience and metadata-only persistence | Passed — automated |
| S05-R07 Revocation/reconciliation | D06, D08 | T07, T10 | PR #124; location/consent/session/device/account/grant lifecycle, bounded cleanup and partial-failure tests | Passed — automated; live revocation not performed |
| S05-R08 Mobile selective receive | D07–D08 | T08–T09 | PR [#125](https://github.com/drakeg/roadtalk/pull/125); fake room events, publication ordering, accessible states and lifecycle cleanup | Passed — automated; physical device not performed |
| S05-R09 Privacy/security | D02–D09 | T01, T04, T06, T08–T09 | exact API/model/migration/config/dependency/log/mobile/evidence gates and private-field rejection | Passed — automated and inspection |
| S05-R10 Reliability/performance | D02–D09 | T02–T10, T12 | boundary/race/replay/churn/failure suites and migrated 100/25/10 PostGIS scale in PR [#126](https://github.com/drakeg/roadtalk/pull/126) | Passed — automated; media NFRs not performed |
| S05-R11 Cost controls | D01, D08–D09 | T11–T12 | disabled zero-resource Terraform, dependency/source scans, operations/evidence and $0 review | Passed — automated and inspection |
| S05-R12 Compatibility/scope | D01–D09 | T09–T12 | complete Sprint 1–4 regressions and later-sprint/prohibited-capability gates | Approved upon review merge |

## Acceptance-test evidence

| Test | Evidence | Result |
|---|---|---|
| S05-T01 | versioned server policy, safe config and rejected client selectors | PASS |
| S05-T02 | migrated PostGIS self/inside/equal/outside/stale/inaccurate/withdrawn/degraded/expired, antimeridian/high-latitude and index-plan fixtures | PASS |
| S05-T03 | sender auth/device/grant/location/audience/rate/concurrency/provider/expiry matrix | PASS |
| S05-T04 | recipient account/device/session/location/consent/grant validity through delivery expiry | PASS |
| S05-T05 | typed auto-subscribe-false provider contract, track lookup and idempotent subscription failures | PASS — synthetic; live provider not performed |
| S05-T06 | owned/foreign/unknown/conflicting track and current-audience publication matrix | PASS |
| S05-T07 | mutation, expiry, revocation, release, disconnect and partial-failure reconciliation | PASS — synthetic; live revocation not performed |
| S05-T08 | fake mobile no-audience/ready/receive/reconciling/denial/release/background/logout/unmount states | PASS — automated; physical device not performed |
| S05-T09 | OpenAPI/database/config/dependency/log/evidence/mobile leakage and scope gates | PASS |
| S05-T10 | full regressions and migrated 100 accounts/25 receivers/10 publishers | PASS — eligible 21.28 ms, denied 2.89 ms, empty-audience 5.79 ms, reconciliation 60.12 ms p95; all ≤400 ms |
| S05-T11 | disabled Terraform zero-resource plans and prohibited dependency/source scans | PASS — $0 current/incremental cost |
| S05-T12 | traceability, synthetic lifecycle, cost/privacy/risk/limitations review and retrospective | APPROVED UPON REVIEW MERGE |

## Authoritative automated baseline

[CI run 31764421021](https://github.com/drakeg/roadtalk/actions/runs/31764421021)
validated D08 commit `ac755f1fb23cb9fc3cb222dcf96ad36a8663a1df`. Backend,
migrated PostGIS, migrations, mobile, dependency, privacy/scope/hardening, disabled
Terraform, TFLint, Trivy, container, and artifact jobs passed. The 100/25/10 scale
output reported 21.28 ms eligible, 2.89 ms denied, 5.79 ms empty-audience, and 60.12 ms
reconciliation p95 against the 400 ms target.

The S05-D09 review CI must pass the same gates. Its green merge is the authoritative
final confirmation and product-owner acceptance event.

## Deliverable audit

| Deliverable | Issue | Pull request/evidence | State |
|---|---:|---|---|
| S05-D01 | #110 | approved specification/readiness #109 and tracker #119 | Complete |
| S05-D02 | #111 | PR #120 | Merged |
| S05-D03 | #112 | PR #121 | Merged |
| S05-D04 | #113 | PR #122 | Merged |
| S05-D05 | #114 | PR #123 | Merged |
| S05-D06 | #115 | PR #124 | Merged |
| S05-D07 | #116 | PR #125 | Merged |
| S05-D08 | #117 | PR #126 | Merged |
| S05-D09 | #118 | traceability and review package | Approved upon merge |

## Evidence boundary

No physical-device microphone/audio route, Bluetooth, interruption, accessibility
gesture, battery, data-use, media latency/jitter/loss, cellular/Wi-Fi, NAT/TURN, live
LiveKit subscription/revocation, AWS deployment/billing/destroy, or automatic-shutdown
evidence was performed. S01-E01 through S01-E03 remain field-test blockers. Synthetic
control-plane timing does not prove WebRTC, network, device, or physical capacity.
