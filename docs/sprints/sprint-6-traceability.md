# Sprint 6 traceability and evidence

- Sprint: 6 — Channels
- Status: Complete upon product-owner merge of the S06-D09 review
- Deliverable: S06-D09
- Issue: #138
- Implementation baseline: merge commit `d720465a3d2629f04e3967a9ba6cbb370c0612dd`
- Evidence date: 2026-08-18

## Status vocabulary

- **Passed — automated:** reproducible repository or GitHub CI checks passed.
- **Passed — inspection:** contracts, documentation, privacy, cost, and scope controls were reviewed.
- **Not performed — field:** requires physical devices, a live provider, or enabled AWS and is not represented as passed.
- **Approved upon merge:** merging the S06-D09 review records the product-owner decision.

## Requirement traceability

| Requirement | Deliverable(s) | Test(s) | Evidence | Status |
|---|---|---|---|---|
| S06-R01 Channel policy/catalog | D01–D02, D06, D08 | T01, T08–T09 | PRs #140, #141 and #145; deterministic General/RV seeds, caller-scoped catalog and privacy gates | Passed — automated and inspection |
| S06-R02 Private-channel lifecycle | D03, D07–D08 | T02, T08–T09 | PRs #142 and #146; create/join/leave/rotate/close API and mobile lifecycle, idempotency and non-disclosing failures | Passed — automated |
| S06-R03 Invite security | D03, D07–D08 | T03, T08–T09 | PRs #142, #146 and #147; entropy, slow-hash/fingerprint, rate-limit, rotation, replay and one-time-display tests | Passed — automated |
| S06-R04 Membership/selection integrity | D02–D05, D08 | T04, T07, T10 | PRs #141–#144 and #147; exactly-one selection, General fallback, serialized races and required grant binding | Passed — automated |
| S06-R05 Channel-bound provider authority | D04–D05, D08 | T05, T07, T09 | PRs #143, #144 and #147; selected-channel/opaque-room grants, least privilege, no room listing/metadata selector | Passed — automated; live provider not performed |
| S06-R06 Channel-and-proximity delivery | D04–D05, D08 | T06–T07, T10 | PRs #143, #144 and #147; same-channel membership/selection matrix plus Sprint 5 proximity predicates and cross-channel denial | Passed — automated; live media not performed |
| S06-R07 Switching/reconciliation | D05–D08 | T07–T10 | PRs #144–#147; revoke-before-switch, active-transmit denial, fresh authority, leave/closure/deletion and bounded partial-failure cleanup | Passed — automated; live revocation not performed |
| S06-R08 Mobile channel experience | D06–D08 | T08–T09 | PRs #145–#147; accessible catalog/private lifecycle, safe transitions, secret cleanup and non-disclosing states | Passed — automated; physical device not performed |
| S06-R09 Privacy/security | D02–D09 | T01–T09, T12 | exact API/model/migration/config/dependency/log/evidence/mobile gates, invite/channel leakage checks and issue #148 scoped Expo follow-up | Passed — automated and inspection |
| S06-R10 Reliability/performance | D02–D09 | T02–T10, T12 | concurrency/replay/race/failure suites and migrated multi-channel 100/25/10 scale in PR #147 | Passed — automated; media/device NFRs not performed |
| S06-R11 Cost controls | D01, D08–D09 | T11–T12 | disabled zero-resource Terraform, dependency/source/container scans, operations/evidence and $0 review | Passed — automated and inspection |
| S06-R12 Compatibility/scope | D01–D09 | T09–T12 | Sprint 1–5 regression gates and prohibited later-sprint/service capability checks | Approved upon review merge |

## Acceptance-test evidence

| Test | Evidence | Result |
|---|---|---|
| S06-T01 | deterministic General/RV seeds, caller-private catalog filtering and non-disclosing schemas | PASS |
| S06-T02 | create/join/leave/rotate/close auth, ownership, idempotency, over-posting and conflict paths | PASS |
| S06-T03 | invite entropy, slow hash/fingerprint, limiter, replay and old/new rotation behavior | PASS |
| S06-T04 | serialized selection races, General fallback and channel-bound grant persistence | PASS |
| S06-T05 | server-derived opaque rooms, exact provider claims and denied client/provider selectors | PASS — synthetic; live provider not performed |
| S06-T06 | current membership/selection crossed with proximity recipient/sender state | PASS — cross-channel delivery denied |
| S06-T07 | switch/transmit races, revoke-before-switch, leave/closure/revocation and partial-failure reconciliation | PASS — synthetic; live revocation not performed |
| S06-T08 | fake mobile catalog/create/join/select/switch/leave/rotate/close, accessibility and cleanup states | PASS — automated; physical device not performed |
| S06-T09 | OpenAPI/database/config/dependency/log/evidence/mobile leakage and scope gates | PASS |
| S06-T10 | full regressions and migrated 100 accounts/25 receivers/10 publishers across General/RV/private | PASS — eligible 35.52 ms, cross-channel denied 3.64 ms, selection/switch 11.97 ms, invite verification 39.20 ms, reconciliation 93.82 ms p95; all ≤400 ms |
| S06-T11 | disabled Terraform zero-resource plans and prohibited dependency/source/container scans | PASS — $0 current/incremental cost |
| S06-T12 | traceability, synthetic lifecycle, cost/privacy/risk/limitations review and retrospective | APPROVED UPON REVIEW MERGE |

## Authoritative automated baseline

D08 pull-request CI run `32211118903` measured the multi-channel control-plane values recorded above. Final D08 CI run `32211306368` on commit `c6c83cdc4eb730c6c53c37b29c3d6c5e6d1e3fa7` passed backend/PostGIS/migrations, mobile, dependency, privacy/scope/hardening, disabled Terraform, TFLint, Trivy, container and artifact gates before PR #147 merged as `d720465a3d2629f04e3967a9ba6cbb370c0612dd`.

The S06-D09 review CI must pass the same gates plus the final Sprint 6 review gate. Its green merge is the authoritative final confirmation and product-owner acceptance event.

## Deliverable audit

| Deliverable | Issue | Pull request/evidence | State |
|---|---:|---|---|
| S06-D01 | #130 | approval/readiness PR #140 and tracker #139 | Complete |
| S06-D02 | #131 | PR #141 | Merged |
| S06-D03 | #132 | PR #142 | Merged |
| S06-D04 | #133 | PR #143 | Merged |
| S06-D05 | #134 | PR #144 | Merged |
| S06-D06 | #135 | PR #145 | Merged |
| S06-D07 | #136 | PR #146 | Merged |
| S06-D08 | #137 | PR #147 | Merged |
| S06-D09 | #138 | traceability and review package | Approved upon merge |

## Evidence boundary

No physical-device microphone/audio route, Bluetooth, interruption, accessibility gesture, battery, data-use, media latency/jitter/loss, cellular/Wi-Fi, NAT/TURN, live LiveKit room isolation/subscription/revocation, AWS deployment/billing/destroy, production capacity, multi-worker correctness, or automatic-shutdown evidence was performed. S01-E01 through S01-E03 remain field-test blockers. Synthetic control-plane timing does not prove WebRTC, network, device, or physical capacity.
