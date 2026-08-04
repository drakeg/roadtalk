# Sprint 4 review record

- Sprint: 4 — Push-to-Talk
- Status: Approved upon merge of this review
- Review date: 2026-08-04
- Deliverable: S04-D09
- Issue: #99
- Acceptance: S04-T12

## Decision requested

Merging this review records product-owner approval of the completed Sprint 4
repository/CI scope and authorizes Sprint 5 planning. It does **not** create or enable
AWS or LiveKit, attach a payment method, approve a paid plan, close Sprint 1 field-test
exceptions, or claim unperformed physical-device/provider evidence.

## Review outcome

S04-D01 through S04-D08 are complete and merged. The implementation provides
metadata-only receive/transmit grants, a disabled-by-default provider boundary,
receive-only join authority, nested microphone-only publication, deterministic mobile
permission/media lifecycles, accessible hold-to-talk behavior, failure-closed
reconciliation, and operational/cost controls.

All repository/CI evidence is green. The product-owner decision
becomes **APPROVED** when this review pull request is merged. Issue #99 and tracker
#100 may then close, and Sprint 5 planning may begin under its own specification and
readiness gate.

## Synthetic demonstration record

Demonstrated without a live provider or physical microphone:

1. an authenticated caller receives one opaque, server-assigned join/subscribe grant;
2. the receive credential denies media/data publication and administrative features;
3. the mobile adapter joins receive-ready with microphone capture disabled;
4. a hold action requests nested, caller-owned, short-lived microphone authority;
5. capture starts only after the exact transmit grant is accepted;
6. a synthetic remote-speaker event produces receiving state without local capture;
7. release disables capture before grant cleanup and provider revocation;
8. expiry, busy, cross-device, malicious, permission, reconnect, lifecycle, and
   provider-ambiguous paths deny or stop publication;
9. session/device/account revocation and bounded reconciliation invalidate stale
   media authority;
10. 100 synthetic accounts, 25 receive-ready participants, and 10 publishers exercise
    eligible and denied grant paths against the 250 ms p95 target in CI.

Detailed mappings are in [Sprint 4 traceability](sprint-4-traceability.md) and
[Sprint 4 synthetic evidence](../evidence/sprint-4/README.md).

## Acceptance results

| Test group | Result | Review evidence |
|---|---|---|
| S04-T01–T05 provider, persistence, receive/transmit, release | PASS | Contract, migration/PostGIS, claim, idempotency, ownership, expiry, concurrency and failure tests |
| S04-T06–T08 mobile permission, receive-ready, hold-to-talk | PASS — automated | Fake native/provider adapters, fake clocks, permission/accessibility and mandatory-stop tests; device evidence pending |
| S04-T09 security/privacy | PASS | Exact OpenAPI/config/dependency/native/database/log/evidence and scope gates |
| S04-T10 reliability/scale | PASS — automated | Full regressions and synthetic 100/25/10 grant-state measurement: eligible 6.57 ms and denied 3.97 ms p95; live media NFRs pending |
| S04-T11 cost/IaC | PASS | Zero-resource Terraform, forbidden-service scans, $10 ceiling and operator stops |
| S04-T12 review | APPROVED UPON MERGE | Traceability, demonstration, cost/privacy/risk, limitations, retrospective and decision |

## Definition of Done

- [x] S04-R01 through S04-R12 implemented and traced
- [x] S04-T01 through S04-T09 and S04-T11 pass within the repository/CI boundary
- [x] S04-D01 through S04-D08 complete and merged
- [x] synthetic receive, authorize, publish, receive, release, denial, expiry and
  failure-closed behavior documented
- [x] no simulated result is represented as physical-device or provider evidence
- [x] current cost, future activation ranges, hard stops, privacy and risks reviewed
- [x] D09 review CI, including S04-T10 synthetic scale, passes
- [ ] S04-D09 review merged and S04-T12 product-owner approval effective
- [ ] issue #99 and Sprint 4 tracker #100 closed as completed

The final two boxes complete operationally through merge. They must not
be represented as complete beforehand.

## Cost decision

**Approved current and incremental cost: $0 AWS + $0 LiveKit per month.** Sprint 4
creates no cloud resource or credential. LiveKit Build device testing may target $0
only after separate approval and within the 3,000-minute, 10 GB, 25-connection, and
$10 cost stops. A bounded scheduled AWS window remains projected at about $4–$6 in an
active testing month and must be destroyed afterward. Always-on AWS, paid LiveKit,
automatic upgrade/scale, and recurring spend above $10 remain prohibited without a
new dated estimate and explicit approval.

## Known limitations and accepted boundaries

- No live LiveKit adapter, project, credential, provider call, or real token
  revocation has been tested.
- Physical-device microphone permission, audio routes/interruption, Bluetooth,
  accessibility gestures, battery, data use, and lifecycle behavior remain unverified.
- Press-to-audible latency, media reconnect, jitter/loss, NAT/TURN, network transition,
  and physical capacity NFRs remain unproven.
- The synthetic scale test measures local grant-service/database behavior; it does
  not prove WebRTC or mobile performance.
- Limiters and reconciliation are process-local/explicit for the approved single-
  worker design. Scaling requires evidence and a new cost decision.
- S01-E01 through S01-E03 remain blockers for any field test.
- Sprint 5 proximity and Sprint 6 channels remain out of scope until separately
  specified and approved.

## Retrospective

What worked:

- server authority, metadata-only storage, permission separation, and stop ordering
  were designed before live-provider integration;
- deterministic provider/native adapters exercised failure and lifecycle paths at $0;
- exact claims, schemas, dependencies, native permissions, logs, evidence, and cost
  gates prevented capability and privacy drift;
- ambiguous provider outcomes revoke local authority first and remain reconcilable;
- operations distinguish $0 implementation, $0 Build testing, scheduled AWS, and
  prohibited always-on/paid stages;
- physical/live claims remain named exceptions instead of simulated evidence.

Improvements:

- include the synthetic scale/p95 measurement earlier in future sprint increments;
- close Sprint 1 physical-device and deployment exceptions before field testing;
- implement a live provider adapter only with its own security, cost, and activation
  review;
- measure media NFRs on representative devices/networks before making low-latency,
  reconnect, battery, or capacity claims;
- preserve the $0 default and require demand/revenue evidence before managed services
  or always-on infrastructure.

## Approval decision and next action

**Decision: approved upon merge.** Merging this review completes S04-D09 and S04-T12,
authorizes closing issue #99 and tracker #100, and permits Sprint 5 planning. It does
not authorize Sprint 5 coding before its specification/readiness approval, and it does
not authorize AWS or LiveKit activation while the named exceptions remain open.
