# Sprint 6 synthetic channel evidence

- Deliverable: S06-D08
- Evidence type: deterministic fakes, migrated-PostGIS CI, zero-resource plans, and repository inspection
- Current and incremental cost: **$0/month**
- AWS/LiveKit resources created: none
- Live-provider, physical-device, and cloud status: **not performed**
- D08 CI: pending authoritative pull-request run
- Eligible, cross-channel denied, selection/switch, invite verification, and reconciliation p95 values must all pass the 400 ms target before merge.

## Automated evidence

| Control | Evidence | Expected result |
|---|---|---|
| Channel privacy and scope | API/schema/migration/config/dependency/source/mobile/evidence gates | No member identity/count, owner identity, private label leakage, invite storage material, provider room/token, proximity detail, audio, transcript, or provider payload is exposed. |
| Invite security | entropy, slow-hash, verification, limiter, rotation, replay, and one-time-display tests | Plaintext appears only on create/rotation success; stored material is non-recoverable and brute-force attempts remain bounded. |
| Channel lifecycle and races | catalog/selection concurrency, active-transmit denial, revoke-before-switch, leave/closure and reconciliation tests | One valid selection remains and prior authority is revoked before state transition; unknown or partial provider state fails closed. |
| Synthetic multi-channel scale | `test_channel_scale.py` on migrated PostGIS | Exactly 100 registered accounts, 25 connected receivers, and 10 active publishers are distributed across General, RV, and private channels; eligible, cross-channel denied, selection/switch, invite verification, and reconciliation p95 values are each at most 400 ms. |
| Cost and dependencies | disabled Terraform plans and prohibited-capability scans | Zero planned resources, no provider calls, and no new paid/managed or later-sprint service dependency. |

The scale output contains aggregate counts and timings only. D09 may link the accepted CI run and transcribe its aggregate p95 values; generated account/device/session, private-channel, room, participant, track, coordinate, invite, and provider values must never be retained as evidence.

## Operations and exceptions

The [channel operations runbook](../../runbooks/channel-operations.md) defines the blocking response for privacy, performance, dependency, configuration, cross-channel, and zero-resource failures. Alerts and CI gates are not automatic shutdown controls.

This evidence does **not** prove real LiveKit room isolation, token revocation, selective subscription, microphone/media delivery, physical-device/network behavior, production capacity, multi-worker correctness, AWS deployment/billing/destroy, billing accuracy, or automatic shutdown. No live LiveKit project, credential, provider call, AWS resource, payment method, or paid plan was used. S01-E01 through S01-E03 remain field-test blockers.
