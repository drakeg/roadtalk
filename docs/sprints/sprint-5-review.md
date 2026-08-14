# Sprint 5 review record

- Sprint: 5 — Proximity Engine
- Status: Approved upon merge of the S05-D09 review
- Review date: 2026-08-14
- Deliverable: S05-D09
- Issue: #118
- Acceptance: S05-T12

## Decision requested

Merging this review records product-owner approval of the completed Sprint 5
repository/CI scope, closes issue #118 and tracker #119 as completed, and authorizes
Sprint 6 planning. It does **not** authorize Sprint 6 coding, AWS or LiveKit activation,
a payment method, a paid plan, recurring spend, or any unperformed field claim.

## Review outcome

S05-D01 through S05-D08 are complete and merged. RoadTalk now has server-controlled
indexed proximity authorization, current recipient eligibility, verified microphone
publication, default-deny selective subscription, lifecycle reconciliation, a mobile
selective-receive experience, and privacy/performance/cost gates. No recipient
membership or proximity detail is exposed or persisted.

All repository/CI evidence is green. The product-owner decision becomes **APPROVED**
when this review PR is merged. Sprint 6 planning may then begin under its own separate
specification and readiness gate.

## Synthetic lifecycle demonstration

Demonstrated without a live provider, physical microphone, or cloud deployment:

1. an authenticated sender with a usable current location and owned receive grant requests a short transmit grant;
2. indexed PostGIS authorization finds only currently valid in-radius opaque receivers;
3. an empty or unknown audience denies promotion without disclosing membership;
4. mobile publishes only after authorization and submits one opaque local microphone track reference;
5. the server verifies room, participant, ownership, microphone source, and active track;
6. eligibility is recomputed and only the current opaque audience is subscribed;
7. mobile renders provider-authorized subscribed audio without selecting tracks;
8. movement, withdrawal, expiry, consent/session/device/account/grant revocation, disconnect, or release moves delivery to denied, ended, or reconciling;
9. partial provider failure denies locally before bounded cleanup and never broadens authorization;
10. migrated PostGIS at 100 accounts, 25 connected receivers, and 10 publishers reports eligible 21.28 ms, denied 2.89 ms, empty-audience 5.79 ms, and reconciliation 60.12 ms p95, all below 400 ms.

## Acceptance results

| Test group | Result | Review evidence |
|---|---|---|
| S05-T01–T04 policy and sender/recipient eligibility | PASS | exact policy/schema plus migrated PostGIS ownership, quality, expiry and boundary matrices |
| S05-T05–T07 provider, publication and reconciliation | PASS — synthetic | deterministic verified-track/subscription, replay/conflict, mutation and partial-failure suites; live provider pending |
| S05-T08 mobile selective receive | PASS — automated | fake room/track events, accessible delivery states and mandatory cleanup; physical device pending |
| S05-T09 privacy/security/scope | PASS | API/model/migration/config/dependency/log/evidence/mobile gates |
| S05-T10 reliability/performance | PASS — automated | full regressions and authoritative 100/25/10 p95 values; physical media/network NFRs pending |
| S05-T11 cost/IaC | PASS | disabled zero-resource Terraform, scans and $0 operations controls |
| S05-T12 final review | APPROVED UPON MERGE | traceability, demonstration, cost/privacy/risk/limitations and retrospective |

## Cost and activation decision

**Approved current and incremental cost: $0 AWS + $0 LiveKit per month.** Sprint 5
created no AWS or LiveKit resource, credential, project, payment method, provider call,
or paid plan. Terraform remains disabled and plans zero resources.

Hard controlled-test stops remain 3,000 participant-minutes, 10 GB downstream transfer,
25 concurrent participants, and $10 total incremental monthly cost. Alerts, budgets,
and quotas are not automatic shutdown controls and never authorize continued spend.
Always-on AWS, paid LiveKit, automatic scaling/upgrades, and recurring spend remain
prohibited without a new dated estimate and explicit product-owner approval.

## Privacy, security, risk, and limitations

- Proximity is an authorization input, never a discovery surface; clients receive no coordinate, radius, distance, direction, exact count, identity, or membership detail.
- Only opaque publication metadata is durable. Eligible participants remain bounded and process-local for provider work.
- Unknown state fails closed. Provider divergence can delay cleanup but cannot restore local authorization; explicit bounded reconciliation remains a single-process design.
- The 100/25/10 result measures synthetic control-plane/PostGIS behavior, not audio, device, network, TURN, battery, or real provider performance.
- No live LiveKit subscription or revocation, physical-device/network behavior, AWS deployment/billing/destroy, or automatic shutdown was tested.
- S01-E01 through S01-E03 remain blockers for field testing.
- Channels, block/mute, maps/routes, background operation, notifications, moderation, recording, transcription, telephony, AI, Redis/RDS/queues/workers/schedulers/WebSockets, self-hosting, and new AWS resources remain out of scope.

## Retrospective

What worked:

- authorizing from current server-side state before designing client states prevented proximity and membership leakage;
- indexed geography, exact provider contracts, deterministic fakes, and lifecycle tests covered boundary and failure behavior at $0;
- separating authorization, publication verification, subscription, and reconciliation made uncertain provider state explicitly fail closed;
- adding the 100/25/10 measurement before final review produced authoritative p95 evidence;
- named field exceptions prevented synthetic results from becoming unsupported claims.

Improvements:

- close Sprint 1 physical-device and deployment exceptions before any field test;
- validate real media/device/network NFRs only in a separately approved bounded window;
- keep p95 categories and privacy leakage gates in every later sprint regression suite;
- revisit single-process reconciliation only with demonstrated scale demand, architecture review, and a new cost decision;
- specify and approve Sprint 6 independently before implementing channel behavior.

## Approval decision and next action

**Decision: approved upon merge of this review PR.** S05-D09 and S05-T12 then become
complete, issue #118 and tracker #119 may close, and Sprint 6 planning may begin. The
merge does not authorize Sprint 6 coding, provider/cloud activation, recurring spend,
or claims beyond the repository/CI evidence boundary.

Detailed mappings are in [Sprint 5 traceability](sprint-5-traceability.md) and
[Sprint 5 synthetic evidence](../evidence/sprint-5/README.md).
