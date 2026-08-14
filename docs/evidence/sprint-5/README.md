# Sprint 5 synthetic proximity evidence

- Deliverable: S05-D08
- Evidence type: deterministic fakes, migrated-PostGIS CI, zero-resource plans, and
  repository inspection
- Current and incremental cost: **$0/month**
- AWS/LiveKit resources created: none
- Live-provider, physical-device, and cloud status: **not performed**
- D08 CI: [run 31764257138](https://github.com/drakeg/roadtalk/actions/runs/31764257138)
- Eligible, denied, empty-audience, and reconciliation p95 values all passed.
- Migrated-PostGIS scale: eligible 21.28 ms, denied 2.89 ms, empty audience
  5.79 ms, and reconciliation 60.12 ms p95; all passed the 400 ms target

## Automated evidence

| Control | Evidence | Result |
|---|---|---|
| Private indexed eligibility | boundary, high-latitude, antimeridian, expiry, consent, device, session, and GiST plan tests | Inclusive `ST_DWithin` authorization returns only opaque in-memory receiver references. |
| Publication and lifecycle | replay/conflict, empty-audience, race, churn, release, expiry, and provider partial-failure suites | Unknown or divergent state fails closed and remains bounded for reconciliation. |
| Mobile boundary | exact transport-shape, fake-room event, background/logout/unmount, and accessibility tests | The client cannot select tracks or audience and mandatory paths stop capture. |
| Privacy and scope | API/schema/migration/config/dependency/source/evidence gates | No coordinate, distance, radius, recipient membership, token, secret, audio, transcript, or provider-payload disclosure is approved. |
| Synthetic scale | `test_ptt_proximity_scale.py` on migrated PostGIS | Exactly 100 accounts, 25 connected receivers, and 10 publishers; eligible 21.28 ms, denied 2.89 ms, empty-audience 5.79 ms, and reconciliation 60.12 ms p95 passed the 400 ms target. |
| Cost | disabled Terraform plans and prohibited-capability scans | Zero planned resources and no new paid or later-sprint capability. |

The scale output contains aggregate counts and timings only. D09 may link the accepted CI
run and transcribe its aggregate p95 values; generated account/device/session, room,
participant, track, coordinate, and provider values must never be retained as evidence.

## Operations and exceptions

The [proximity operations runbook](../../runbooks/proximity-operations.md) defines the
blocking response for privacy, performance, dependency, configuration, and zero-resource
failures. Alerts and CI gates are not automatic shutdown controls.

This evidence does **not** prove real microphone/media delivery, LiveKit subscription or
revocation, physical-device/network behavior, AWS deployment/billing/destroy, billing
accuracy, or automatic shutdown. No live LiveKit project, credential, provider call, AWS
resource, payment method, or paid plan was used. S01-E01 through S01-E03 remain field-test
blockers.
