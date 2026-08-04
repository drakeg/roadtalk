# Sprint 4 synthetic Push-to-Talk evidence

- Deliverable: S04-D08
- Evidence type: deterministic automated tests, zero-resource plans, and repository inspection
- Baseline: merge commit `f98676ae48a758fbfe9bb723fcd253945145f79c`
- D07 CI: [run 30867485264](https://github.com/drakeg/roadtalk/actions/runs/30867485264)
- D08 CI: [run 30872097026](https://github.com/drakeg/roadtalk/actions/runs/30872097026)
- D09 CI and measured grant p95: [run 30872939267](https://github.com/drakeg/roadtalk/actions/runs/30872939267) — eligible 6.57 ms; denied 3.97 ms
- D09 final confirmation: [run 30873126123](https://github.com/drakeg/roadtalk/actions/runs/30873126123)
- AWS/LiveKit resources created: none
- Current and incremental cost: **$0/month**
- Live-provider and physical-device status: **not performed**

## Synthetic lifecycle demonstration

All provider behavior uses generated references, fake clocks, an injected deterministic
provider, local/PostGIS test data, and CI. Evidence retains test names and stable
outcomes only; it does not retain generated values.

| Capability | Automated/repository evidence | Demonstrated result |
|---|---|---|
| Receive-only authority | provider-claim, service, route, database, and mobile grant tests | One caller/device receives one-room join/subscribe authority; publication, data, admin, recording, ingress, and egress claims are absent. |
| Nested transmit authority | transmit service/API/database and mobile transport tests | Capture cannot start before a caller-owned, microphone-only, short-lived transmit grant. |
| One publisher and bounded access | concurrency, idempotency, expiry, cross-device, over-posting, and limiter tests | Duplicate work is stable, unknown authority fails closed, and active publishing is bounded. |
| Hold/release safety | fake-clock controller and accessibility screen tests | Release, 30-second maximum, background, exit, logout, reconnect, failure, and unmount stop capture before cleanup. |
| Provider divergence | `test_ptt_hardening.py` and database ambiguous-failure cases | Local authority is revoked before provider cleanup; failed cleanup remains durable and bounded for later reconciliation. |
| Stale participants | bounded reconciliation success/partial/failure tests | Expired or cleanup-pending participants are denied publication and removed when required without reauthorization. |
| Session/device/account revocation | auth unit/integration and database cascade tests | Refresh replay, logout, device revocation, and account deletion invalidate media metadata. |
| Metadata-only privacy | schema/migration inspection, closed logging tests, and PTT privacy gate | No token, secret, audio, transcript, listener, callsign, or coordinate column/log/evidence path is approved. |
| Configuration/dependencies | Settings tests, dependency allowlists, Expo Doctor, npm/pip audits | Live configuration is disabled; CI has no provider credential/network call or paid/background capability. |
| Zero-resource cost | disabled Terraform plans, TFLint/Trivy, cost guardrails, and operations gate | Default plans create zero resources; the notification budget is capped at $10; prohibited managed services remain absent. |
| Prior-sprint compatibility | full backend/mobile/privacy/security/migration/container CI jobs | Sprint 1–3 authentication, identity, recovery, location, privacy, and infrastructure gates remain green. |
| Synthetic field-test grant scale | `test_ptt_scale.py` with migrated PostgreSQL | 100 registered accounts, 25 connected receivers, 10 active publishers, 95 eligible requests at 6.57 ms p95, and 10 busy denials at 3.97 ms p95 passed the 250 ms target. |

## S04-D08 cost-control evidence

- [PTT operations](../../runbooks/ptt-operations.md) separates $0 implementation,
  $0 Build testing, scheduled AWS windows, and prohibited always-on/paid stages.
- Hard stops are 3,000 participant-minutes, 10 GB downstream transfer, 25 concurrent
  participants, and $10 incremental monthly cost.
- Crossing a stop pauses testing and cannot trigger an automatic plan upgrade,
  payment-method change, quota increase, AWS resize, or scale-out.
- The scheduled-test template requires a dated pre-cost check, exact approved window,
  destroy owner, post-destroy zero-resource plan, independent inventory, and delayed
  billing follow-up.
- `scripts/ci/check-ptt-operations.py` rejects missing stop language, a Terraform
  notification budget above $10, missing evidence boundaries, and missing CI enforcement.

## Privacy-safe reproduction

Use repository test targets and GitHub CI. Record only the commit, workflow URL,
test/gate name, pass/fail result, aggregate metrics, route template, and stable problem
code where necessary.

Never paste or commit raw participant tokens, API keys/secrets, authorization headers,
request/response bodies, audio, transcripts, callsigns, coordinates, account/device/
session IDs, room/participant references, public IPs, unrestricted logs, screenshots
containing values, or database dumps. Synthetic markers are test inputs, not retained
evidence.

## Named exceptions and unproven claims

This evidence does **not** prove:

- real iOS/Android permission, audio-route, interruption, Bluetooth, or accessibility gesture behavior;
- real microphone/audio quality, latency, jitter, packet loss, battery, or data use;
- cellular/Wi-Fi transition, restrictive NAT/TURN, reconnect, or provider token revocation;
- a live LiveKit project, live credential, provider call, enabled AWS plan, deployment,
  automatic shutdown, billing accuracy, or physical-device field test.

Those remain explicit pending exceptions behind the applicable Sprint 1 gates and a
separately approved test record. Use the
[physical-device media template](physical-device-media-test-template.md) and
[scheduled cloud test template](scheduled-cloud-test-record-template.md) only after approval.

## Final review

The complete approved requirement, acceptance-test, and deliverable mapping is in
[Sprint 4 traceability](../../sprints/sprint-4-traceability.md). The product-owner
decision was recorded by merged PR #108 through the
[Sprint 4 review](../../sprints/sprint-4-review.md). Review approval did not activate a
provider or cloud environment.
