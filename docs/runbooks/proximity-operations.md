# Sprint 5 proximity operations

- Deliverable: S05-D08
- Current and incremental cost: **$0 AWS + $0 LiveKit per month**
- Execution boundary: local development and GitHub CI with deterministic fakes and a
  disposable migrated PostGIS service

## Safe operating state

Terraform remains disabled and its default plans must create zero resources. The media
provider remains disabled, no credential is configured, and no provider or AWS call is
part of this runbook. CI may use its ephemeral PostGIS container; it must not use RDS,
Redis, a queue, worker, scheduler, WebSocket service, recording, egress, transcription,
telephony, agents, or self-hosting.

Before accepting a change, run the full backend and mobile suites, the Sprint 5 privacy
and hardening gates, dependency/config/source scans, and disabled Terraform validation.
The migrated-PostGIS scale test must retain exactly 100 accounts, 25 connected receivers,
and 10 active publishers. Eligible, denied, empty-audience, and reconciliation p95 values
must each remain at or below the 400 ms control-plane target.

## Failure and containment

- A failed authorization, privacy, race, replay, partial-provider, or reconciliation test
  blocks merge. Unknown state remains locally denied or reconciling.
- A p95 result above 400 ms blocks merge. Record only the aggregate category and timing;
  never retain coordinates, distance, radius, membership, identifiers, tokens, provider
  payloads, logs containing markers, audio, or transcripts.
- A non-zero disabled Terraform plan, new paid/later-sprint capability, provider call, or
  credential blocks merge and requires inspection. Do not apply or activate anything.
- The npm `image-size` exception is limited to its two recorded advisories and expires on
  2026-09-30; any other high/critical finding still blocks CI.

No budget alert or CI check is an automatic shutdown control. There is nothing to destroy
in this $0 workflow. Any live/device/cloud test, recurring spend, payment method, or
provider/AWS activation requires a new dated estimate and explicit product-owner approval.

## Named exceptions

This runbook does not prove real microphone/media delivery, LiveKit subscription or
revocation, physical-device/network behavior, AWS deployment/billing/destroy, or automatic
shutdown. S01-E01 through S01-E03 remain field-test blockers.
