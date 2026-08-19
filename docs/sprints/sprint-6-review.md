# Sprint 6 review record

- Sprint: 6 — Channels
- Status: Approved upon merge of the S06-D09 review
- Review date: 2026-08-18
- Deliverable: S06-D09
- Issue: #138
- Acceptance: S06-T12

## Decision requested

Merging this review records product-owner approval of the completed Sprint 6 repository/CI scope, closes issue #138 and tracker #139 as completed, and permits the next RoadTalk planning decision. It does **not** authorize Sprint 7 coding, AWS or LiveKit activation, a payment method, a paid plan, recurring spend, production/public beta, or any unperformed field claim.

## Review outcome

S06-D01 through S06-D08 are complete and merged. RoadTalk now has server-seeded General/RV channels, invite-only private channels, one authoritative account selection, secure invite lifecycle, channel-bound media/proximity authorization, revoke-before-switch reconciliation, and accessible mobile channel management. Channel membership, invite material, provider room detail, and proximity state remain non-disclosing.

All repository/CI evidence is green. The product-owner decision becomes **APPROVED** when this review PR is merged. What comes next should be planned separately from this acceptance event; this review does not silently authorize Route Awareness, web, cloud/provider activation, or an alpha deployment.

## Synthetic channel lifecycle demonstration

Demonstrated without a live provider, physical microphone, or cloud deployment:

1. a new authenticated account defaults to the server-seeded General channel;
2. the caller may list General, RV, and only private channels for which it has active membership;
3. private-channel creation returns one high-entropy invite once while durable storage retains only a slow hash and non-secret fingerprint;
4. a valid invite creates membership without exposing the creator or other members; rotation invalidates the old secret and closure removes authorization;
5. selecting an authorized channel is account-wide, serialized, idempotent, and server-authoritative;
6. switching, leaving, closure, deletion, or revocation locally removes old channel-bound media authority before changing durable selection state;
7. fresh receive/transmit authority is bound to the selected channel and server-derived opaque room; clients cannot choose provider rooms or elevated permissions;
8. proximity authorization adds exact current same-channel membership/selection to every Sprint 5 sender/recipient rule, so cross-channel delivery fails closed;
9. mobile stops capture/subscriptions before transitions, reconnects from fresh server state, and exposes no member identity/count, invite fingerprint, provider room, or proximity detail;
10. migrated PostGIS at 100 accounts, 25 connected receivers, and 10 publishers distributed across General, RV, and private channels reports eligible 35.52 ms, cross-channel denied 3.64 ms, selection/switch 11.97 ms, invite verification 39.20 ms, and reconciliation 93.82 ms p95, all below 400 ms.

## Acceptance results

| Test group | Result | Review evidence |
|---|---|---|
| S06-T01–T04 catalog/private lifecycle/invite/selection | PASS | deterministic seeds, exact caller-scoped APIs, secure invite handling, idempotency/concurrency and General fallback |
| S06-T05–T07 provider/channel/proximity/reconciliation | PASS — synthetic | opaque channel-room binding, same-channel proximity matrix, revoke-before-switch and bounded partial-failure cleanup; live provider pending |
| S06-T08 mobile channel experience | PASS — automated | accessible catalog/private management, one-time secret cleanup, safe transitions and non-disclosing errors; physical device pending |
| S06-T09 privacy/security/scope | PASS | API/model/migration/config/dependency/log/evidence/mobile hardening gates |
| S06-T10 reliability/performance | PASS — automated | full regressions and authoritative multi-channel 100/25/10 p95 values; physical media/network NFRs pending |
| S06-T11 cost/IaC | PASS | disabled zero-resource Terraform, dependency/source/container scans and $0 operations controls |
| S06-T12 final review | APPROVED UPON MERGE | traceability, demonstration, cost/privacy/risk/limitations and retrospective |

## Cost and activation decision

**Approved current and incremental cost: $0 AWS + $0 LiveKit per month.** Sprint 6 created no AWS or LiveKit resource, credential, project, payment method, provider call, or paid plan. Terraform remains disabled and plans zero resources.

Hard controlled-test stops remain 3,000 participant-minutes, 10 GB downstream transfer, 25 concurrent participants, and $10 total incremental monthly cost. Alerts, budgets, CI checks, and quotas are not automatic shutdown controls and never authorize continued spend. Always-on AWS, paid LiveKit, automatic scaling/upgrades, and recurring spend remain prohibited without a new dated estimate and explicit product-owner approval.

## Privacy, security, risk, and limitations

- Public discovery is limited to General and RV; private channels are caller-member-only and expose no member identity, list, count, creator, invite fingerprint/hash, or provider room.
- Private display text is member-visible only and excluded from routine logs, metrics, and evidence.
- Invite plaintext is intentionally one-time and unrecoverable; losing it requires creator rotation rather than support recovery.
- Channel selection and room references are server-authoritative. LiveKit room separation is defense in depth, not RoadTalk's authorization source.
- Unknown or partial provider state fails closed. Reconciliation is bounded and remains a single-process design.
- The 100/25/10 result measures synthetic control-plane/PostGIS behavior, not audio, device, network, TURN, battery, or real provider performance.
- No live LiveKit room isolation/subscription/revocation, physical-device/network behavior, AWS deployment/billing/destroy, production capacity, multi-worker correctness, or automatic shutdown was tested.
- S01-E01 through S01-E03 remain blockers for field testing.
- Presence/WebSockets, maps/routes, notifications, block/mute/reporting/moderation, messaging, background/hands-free behavior, recording/transcription/translation/telephony/AI, Redis/RDS/queues/workers/schedulers, self-hosting, and new AWS resources remain out of Sprint 6 scope.
- Issue #148 tracks the four patch-level Expo SDK packages whose recommendation advanced during D08 validation. The scoped Expo Doctor package exclusions are temporary and must be removed when that lockfile refresh is completed.

## Retrospective

What worked:

- keeping channel selection and provider-room derivation server-side prevented private membership and provider topology from becoming client policy;
- composing channel authorization with the already accepted proximity rules avoided a parallel delivery model;
- revoke-before-switch plus explicit reconciliation made channel changes fail closed under races and partial provider failure;
- one-time invite disclosure, slow-hash storage, and non-disclosing failure responses preserved anonymous-account privacy without adding contact/member-directory scope;
- mobile lifecycle tests forced capture and subscriptions to stop before channel state transitions;
- extending the 100/25/10 test across General, RV, and private channels produced direct cross-channel performance evidence while retaining the $0 boundary.

Improvements:

- close Sprint 1 physical-device and deployment exceptions before any field test;
- refresh the four Expo SDK patch packages in issue #148 and remove the temporary Doctor exclusions;
- validate real channel switching, media isolation, microphone/audio and device/network NFRs only in a separately approved bounded live window;
- keep channel leakage, cross-channel denial, p95 categories, zero-resource plans, and full prior-sprint regressions in later sprint gates;
- revisit single-process reconciliation only with demonstrated scale demand, architecture review, and a new cost decision;
- make the next planning decision explicitly account for the stated goal of reaching a usable alpha soon rather than assuming every later roadmap sprint is a release prerequisite.

## Approval decision and next action

**Decision: approved upon merge of this review PR.** S06-D09 and S06-T12 then become complete, issue #138 and tracker #139 may close, and Sprint 6 becomes accepted. The merge does not authorize Sprint 7 coding, provider/cloud activation, recurring spend, public/field deployment, or claims beyond the repository/CI evidence boundary.

Detailed mappings are in [Sprint 6 traceability](sprint-6-traceability.md) and [Sprint 6 synthetic evidence](../evidence/sprint-6/README.md).
