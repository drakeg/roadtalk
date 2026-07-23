# Sprint 4 readiness

- Sprint: 4 — Push-to-Talk
- Status: NOT READY — awaiting product-owner approval
- Planning issue: #90
- Planning date: 2026-07-16
- Proposed baseline: Sprint 3 approval merge from PR #89

## Decision

Sprint 4 is fully specified for a zero-spend local/GitHub CI implementation, but code
is **not authorized** until the product owner approves
`sprint-4-push-to-talk.md`, this readiness record, and the cost boundary in issue
#90.

After approval, implementation may use deterministic provider fakes and synthetic
tokens/events. LiveKit Cloud and AWS remain disabled. Live-provider, physical-device,
and field-test work requires separate activation authority and closure of applicable
Sprint 1 exceptions.

## Definition of Ready

- [x] Sprint 3 review is merged, deliverable #80 is closed, and tracker #81 is closed.
- [x] Roadmap objective is explicit: low-latency voice streaming.
- [x] Sprint 4 is separated from Sprint 5 proximity and Sprint 6 channels.
- [x] One server-assigned controlled test room provides a bounded integration context.
- [x] Receive-only join and microphone-only transmit permission are separated.
- [x] Hold-to-talk, maximum duration, release, expiry, disconnect, background, logout,
  permission-revocation, and unmount stop conditions are explicit.
- [x] Requirements S04-R01–R12, acceptance tests S04-T01–T12, and deliverables
  S04-D01–D09 are proposed.
- [x] ADR-0004's LiveKit Cloud, audio-only, no-storage decision remains controlling.
- [x] LiveKit Cloud permission updates allow receive-ready clients to transmit without
  reconnecting on every press.
- [x] Server-only secret, least-privilege token, opaque identity/room, remote-unmute,
  failure-closed, idempotency, rate, and concurrency rules are specified.
- [x] Microphone permission and accessible mobile state boundaries are specified.
- [x] Recording, egress, transcription, telephony, agents, background audio, Redis,
  RDS, workers, extra AWS resources, proximity, and channels are excluded.
- [x] Synthetic versus live/device evidence is separated honestly.
- [x] Current LiveKit pricing, hard free-tier quotas, paid-plan floor, stop thresholds,
  combined AWS/media scenarios, and budgets are documented.
- [x] Planning approval, code authorization, provider activation, AWS activation, and
  paid-plan approval are separate gates.
- [ ] Product owner approves the proposed Sprint 4 specification/readiness/cost
  baseline in issue #90.
- [ ] S04-D01 tracker and scoped implementation issues are created from approved text.
- [ ] Repository status is updated to make Sprint 4 the sole active implementation
  sprint.

## Architecture gate

The proposed implementation follows ADR-0004 and current official LiveKit behavior:

- a receive token grants room join and subscribe, with `canPublish=false` and data,
  room-admin, recording, and egress permissions absent;
- on press, RoadTalk reauthorizes and uses the server API to update the connected
  participant to `canPublish=true` and `canPublishSources=[microphone]`;
- on release/revocation, removing publish permission unpublishes active tracks;
- LiveKit Cloud revokes stale tokens when participant permissions change or a
  participant is removed;
- the mobile client still owns microphone capture and starts it only after
  authorization; remote unmute remains disabled;
- provider operations sit behind a typed interface, with deterministic fakes in CI;
- audio never passes through FastAPI or PostgreSQL.

The implementation must lock the final OpenAPI route shape before route code. The two
acceptable shapes are a mode field on `POST /ptt/grants` or a nested transmit action
under the caller's receive grant. Neither may change the approved authorization or
data-minimization boundary.

## Security and privacy gate

- No live LiveKit API key, API secret, URL, project, or participant token in source,
  fixtures, logs, CI variables, screenshots, evidence, or mobile configuration.
- Synthetic token tests use unmistakably fake secrets and decoded-claim assertions.
- Provider credentials are injected server-side only after separate activation
  approval.
- The database stores metadata-only grant state; raw signed tokens, audio, transcript,
  exact listener membership, and exact location have no persistence path.
- Provider room and participant identifiers are random/opaque and do not encode
  callsign, account ID, device ID, coordinates, or channel.
- Only microphone track publication can be granted. Data/camera/screen/recording/
  egress/admin capabilities are prohibited.
- Capture never begins before explicit user press plus server/provider authorization.
- Capture stops before the release request and on every lifecycle/permission/security
  exit.
- Routine diagnostics use the existing closed-field logging policy. Request/response
  bodies and provider payloads are not logged.
- Unknown authorization, provider timeout, ambiguous update, expired grant, or stale
  participant state fails closed.

## Mobile and platform gate

The LiveKit Expo SDK requires native code and is not compatible with Expo Go. Sprint 4
therefore uses the existing Expo development-build posture and pins a dependency set
compatible with the repository's supported Expo SDK.

Before merging the mobile foundation:

- Expo Doctor and native configuration checks pass;
- microphone usage strings are purpose-accurate;
- no `UIBackgroundModes=audio`, background service, wake lock, camera permission, or
  unrelated sensitive permission is introduced;
- unasked, granted, denied, blocked, unavailable, and changed-in-settings states are
  tested;
- the room/audio adapter is fakeable without native code in ordinary unit tests;
- screen exit, background, logout, device revocation, account deletion, connection
  failure, and unmount deterministically stop/disconnect;
- physical-device audio route, interruption, Bluetooth, cellular, NAT, battery, and
  latency outcomes remain pending until real evidence exists.

## Reliability and evidence gate

Synthetic acceptance may prove:

- grant claims and authorization order;
- state-machine ordering;
- idempotency, rate/concurrency behavior, expiry, revocation, and failure handling;
- provider request shape;
- mobile lifecycle cancellation;
- logging/database/privacy invariants;
- API grant latency under local load;
- disabled Terraform and zero cloud calls.

Synthetic acceptance may not claim:

- press-to-audible NFR-01;
- media reconnect NFR-04;
- physical capacity NFR-07;
- battery NFR-09;
- audio data rate NFR-10;
- real microphone permission/store behavior;
- real provider token revocation;
- cellular, Wi-Fi transition, restrictive NAT/TURN, Bluetooth, interruption, or
  background behavior.

Those claims require an approved LiveKit Build project, physical devices, controlled
scripts, and named evidence records. Open Sprint 1 exceptions remain field-test
blockers.

## Cost gate

RoadTalk's zero-revenue policy makes **$0/month** the default target and **$10/month**
the initial hard recurring-cost ceiling.

### Default implementation

- AWS resources created: **none**
- LiveKit resources created: **none**
- AWS monthly cost: **$0**
- LiveKit monthly cost: **$0**
- Incremental monthly cost: **$0**
- CI provider calls: **zero**
- Terraform default: disabled, zero resources
- Payment method or automatic provider upgrade: **prohibited**

### Approved sequencing

1. Implement and accept Sprint 4 locally and in GitHub CI at $0.
2. Use LiveKit Build only after separate physical-device activation approval; keep the
   backend local where practical so this stage remains $0.
3. When remote backend testing is necessary, use scheduled AWS test windows rather
   than a continuously running environment.
4. Stop or destroy the AWS test stack after the approved script. Retain storage only
   through an explicit decision that accepts its monthly charge.
5. Do not run an always-on public environment until measured demand, funding, or a
   viable revenue path justifies it.

### Planning scenarios

| Scenario | Projected monthly cost | Gate |
|---|---:|---|
| Code/CI only | **$0** | Default |
| LiveKit Build device test, AWS off | **$0** | Separate test approval |
| Scheduled AWS testing | **about $4–$6 in an active test month** | Must remain below $10 ceiling |
| Inactive month, stack destroyed | **$0** | Preferred |
| Inactive month, storage retained | **about $3–$5** | Explicit retention decision |
| Always-on AWS + Build | **$8–$11 during eligible promotion; $20–$23 afterward** | New approval; not Sprint 4 default |
| Always-on AWS + Ship | **$58–$61+ during eligible promotion; $70–$73+ afterward** | Paid-plan decision; prohibited by default |

Scheduled estimates are planning ranges, not guarantees. Recalculate the exact
Terraform plan, hours, storage, monitoring, backups, public IPv4, transfer, taxes, and
current provider pricing before activation.

LiveKit Build's published free limits are 5,000 participant-minutes, 50 GB downstream
transfer, and 100 concurrent connections. RoadTalk's lower stops remain 3,000 minutes,
10 GB, and 25 connections. Crossing a limit pauses testing; it never authorizes Ship.

RDS, managed Redis, NAT Gateway, ALB, Fargate, paid monitoring, recording, egress,
transcription, agents, telephony, enhanced paid processing, self-hosting, automatic
scaling, payment-method attachment, and automatic plan upgrades are prohibited.

Any projected recurring spend above **$10/month** requires a dated cost estimate and
explicit product-owner approval before implementation or activation.

## Sprint 1 exception boundary

S01-E01 through S01-E03 remain open. Sprint 4 local/CI implementation may proceed only
after planning approval, but no real microphone, native audio route, physical latency,
battery/data, cellular/NAT, live provider, enabled AWS plan, deployment, or field-test
operation may be represented as passed until each prerequisite exception is closed
and evidence is recorded.

## Preconditions before the first code change

1. [ ] Product owner explicitly approves `sprint-4-push-to-talk.md`, this readiness
   record, and the cost boundary in issue #90.
2. [ ] Planning issue #90 is updated/closed as completed.
3. [ ] Tracker and S04-D01 through S04-D09 issues are created from the approved wording.
4. [ ] Documentation status names Sprint 4 as the sole active implementation sprint.
5. [ ] The final approval update on `main` is recorded as the implementation baseline.
6. [ ] S04-D01 planning/setup is complete; code begins with S04-D02 using the normal
   branch/PR workflow.
7. [x] Terraform, LiveKit provider calls, and live credentials remain disabled.
8. [x] Sprint 1 exceptions remain visible as live/device/field-test blockers.

## Readiness conclusion

**NOT READY.** The technical, privacy, security, evidence, and cost boundaries are
complete, and the default implementation cost is $0. Product-owner approval in issue
#90 is the remaining decision. Approval will authorize tracker creation and local/CI
coding only; cloud activation and any paid plan remain separate decisions.

## Primary references

- [LiveKit pricing](https://livekit.com/pricing)
- [LiveKit quotas and limits](https://docs.livekit.io/deploy/admin/quotas-and-limits/)
- [LiveKit Cloud billing](https://docs.livekit.io/deploy/admin/billing/)
- [LiveKit Expo quickstart](https://docs.livekit.io/transport/sdk-platforms/expo/)
- [LiveKit tokens and grants](https://docs.livekit.io/home/server/generating-tokens/)
- [LiveKit participant management](https://docs.livekit.io/intro/basics/rooms-participants-tracks/participants/)
