# Sprint 6 synthetic channel evidence

- Deliverable: S06-D08
- Evidence type: deterministic fakes, migrated-PostGIS CI, zero-resource plans, and repository inspection
- Current and incremental cost: **$0/month**
- AWS/LiveKit resources created: none
- Live-provider, physical-device, and cloud status: **not performed**
- D08 authoritative CI: pull-request run `32211118903` on 2026-08-19
- Backend suite: 209 passed, 89.96% branch coverage
- Mobile quality: Expo Doctor, TypeScript, and Jest passed
- Eligible p95: **35.52 ms**
- Cross-channel denied p95: **3.64 ms**
- Selection/switch p95: **11.97 ms**
- Invite verification p95: **39.20 ms**
- Reconciliation p95: **93.82 ms**
- Control-plane target: **400 ms**; every measured Sprint 6 category passed.

## Automated evidence

| Control | Evidence | Result |
|---|---|---|
| Channel privacy and scope | API/schema/migration/config/dependency/source/mobile/evidence gates | Passed; no member identity/count, owner identity, private label leakage, invite storage material, provider room/token, proximity detail, audio, transcript, or provider payload is exposed. |
| Invite security | entropy, slow-hash, verification, limiter, rotation, replay, and one-time-display tests | Passed; plaintext appears only on create/rotation success, stored material is non-recoverable, and brute-force attempts remain bounded. |
| Channel lifecycle and races | catalog/selection concurrency, active-transmit denial, revoke-before-switch, leave/closure and reconciliation tests | Passed; one valid selection remains and prior authority is revoked before state transition; unknown or partial provider state fails closed. |
| Synthetic multi-channel scale | `test_channel_scale.py` on migrated PostGIS | Passed with exactly 100 registered accounts, 25 connected receivers, and 10 active publishers distributed across General, RV, and private channels. All five p95 categories remained below 400 ms. |
| Cost and dependencies | disabled Terraform plans and prohibited-capability scans | Passed; zero planned resources, no provider calls, and no new paid/managed or later-sprint service dependency. |

The scale output contains aggregate counts and timings only. Generated account/device/session, private-channel, room, participant, track, coordinate, invite, and provider values are not retained as evidence.

## Operations and exceptions

The [channel operations runbook](../../runbooks/channel-operations.md) defines the blocking response for privacy, performance, dependency, configuration, cross-channel, and zero-resource failures. Alerts and CI gates are not automatic shutdown controls.

The Expo SDK 57 metadata recommendation advanced while this D08 PR was under validation. Issue #148 records the follow-up lockfile refresh for four patch-level Expo packages. This PR keeps the existing locked versions and uses Expo's package-version-check exclusion only for those four packages; Expo Doctor's remaining checks, TypeScript, Jest, dependency audits, and security gates remain enforced.

This evidence does **not** prove real LiveKit room isolation, token revocation, selective subscription, microphone/media delivery, physical-device/network behavior, production capacity, multi-worker correctness, AWS deployment/billing/destroy, billing accuracy, or automatic shutdown. No live LiveKit project, credential, provider call, AWS resource, payment method, or paid plan was used. S01-E01 through S01-E03 remain field-test blockers.
