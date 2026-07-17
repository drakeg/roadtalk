# Sprint 4: Push-to-Talk

## Status

Proposed — awaiting product-owner approval in issue #90. Planning only; no code or
cloud activation is authorized.

## Objective

Allow authenticated RoadTalk clients in a controlled, server-assigned test room to
join receive-ready and exchange low-latency, audio-only, hold-to-talk voice through
LiveKit, while RoadTalk retains grant authority and never stores, records, transcribes,
proxies, or logs audio.

## Product decisions

- Sprint 4 validates the media and interaction foundation only. One opaque,
  server-assigned controlled test room replaces user-selected channels and nearby
  delivery until Sprints 5 and 6.
- A client first obtains a receive-only grant and joins LiveKit with microphone capture
  off. Receiving does not imply permission to publish.
- Pressing and holding the PTT control requests a short publishing grant for the
  already-connected participant. RoadTalk uses LiveKit participant-permission updates
  to allow microphone publication without a room reconnect.
- Releasing, cancelling, losing microphone permission, leaving the foreground, losing
  authentication, disconnecting, or reaching the grant deadline stops capture and
  revokes publication. An expiry is a safety backstop, not the normal release path.
- The initial maximum transmission duration is 30 seconds. The value is versioned
  server policy and may change only with evidence and approval.
- Only microphone tracks may be published. Camera, screen share, data tracks,
  recording, egress, transcription, telephony, agents, and remote unmute are disabled.
- One active publishing grant is allowed per account and device. Contention fails
  closed with a stable busy response; no queue or hands-free mode is introduced.
- LiveKit participant identity, room name, and grant references are opaque and derived
  server-side. Callsigns and account/device identifiers are not used as provider
  identifiers.
- Microphone permission is requested only after a purpose explanation and explicit
  action. Denial preserves identity, location settings, and other non-audio features.
- Audio flows directly between mobile clients and LiveKit Cloud over WebRTC. The
  RoadTalk API never receives audio packets.
- LiveKit Cloud is not provisioned during code implementation. Local and CI tests use
  fakes and synthetic media events. Real-device/cloud evidence requires separate
  activation approval and closure of applicable Sprint 1 exceptions.

These decisions prove Sprint 4's low-latency voice-streaming objective without
implementing Sprint 5 proximity or Sprint 6 channel semantics early.

## Representative control flow

1. An authenticated mobile client explicitly opens the controlled PTT experience.
2. The RoadTalk API validates the session, device, policy version, test eligibility,
   rate limit, and provider configuration.
3. The API persists metadata for a short-lived receive grant and signs a LiveKit token
   with room join, subscribe, no data publication, and no media publication.
4. The mobile client joins the opaque room and starts the communication audio session
   without starting microphone capture.
5. On press-and-hold, the client requests a publishing grant for its active receive
   grant.
6. The API revalidates the session and concurrency policy, records an expiring
   metadata-only publishing grant, and updates that LiveKit participant to
   `canPublish=true` with `canPublishSources=[microphone]`.
7. After permission confirmation, the client enables its microphone track and shows a
   non-color-only TRANSMITTING state.
8. Other connected test participants receive the audio track and an opaque technical
   participant reference; identity presentation remains limited to approved RoadTalk
   data.
9. Release or any mandatory stop condition disables microphone capture first, then
   calls the RoadTalk release endpoint. The API revokes publish permission and marks
   the grant ended.
10. Unknown or inconsistent state fails closed. Provider reconciliation removes
    publication on the next bounded action without requiring Redis or a scheduler.
11. Technical outcome data may record timestamps, duration class, stable termination
    code, and aggregate quality metrics. It never contains audio, transcript, token,
    coordinates, or precise listener membership.

## API boundary

The approved `/api/v1/ptt/grants` resource supports two server-controlled modes:

- `receive`: creates a short-lived room-join grant with subscribe permission and no
  publication permission;
- `transmit`: requires the caller's active receive grant, creates one expiring
  publisher grant, and promotes the existing participant to microphone-only publish.

`DELETE /api/v1/ptt/grants/{grant_id}` releases the caller-owned receive or transmit
grant. Deleting a transmit grant revokes publish permission and unpublishes any active
track. Deleting a receive grant removes the participant and all related active grants.

Requests accept an `Idempotency-Key`. Ownership always comes from the authenticated
session; clients cannot select accounts, devices, room names, participant identities,
provider URLs, permissions, TTLs, or policy versions.

Responses may contain:

- opaque RoadTalk grant ID;
- LiveKit URL and a short-lived participant token for a receive grant only;
- opaque room/participant references;
- allowed actions and track sources;
- issued/expiry timestamps;
- policy version;
- reconnect instruction.

Responses never contain LiveKit API keys/secrets, account/device IDs, coordinates,
nearby membership, provider administrative tokens, or signed tokens after the initial
receive response. Raw provider tokens are never persisted.

The API surface may add an explicit `POST /ptt/grants/{receive_grant_id}/transmit`
alias during implementation if OpenAPI review shows it is clearer than a mode field;
either shape must preserve the same authorization, idempotency, and ownership rules
and be locked before route implementation.

## Requirements

- **S04-R01 — Provider boundary:** Implement a typed LiveKit media-control interface
  for token creation, participant permission updates, participant removal, and
  provider failures. Production calls are disabled unless all explicit configuration
  gates pass; unit and CI tests use a deterministic fake.
- **S04-R02 — Metadata-only grants:** Persist opaque receive/transmit grant records
  with account/device ownership, opaque provider room/participant references, action
  scope, policy version, issued/expiry/revoked timestamps, and stable outcome codes.
  Never persist signed tokens, provider secrets, audio, transcripts, or listener
  membership. Expired state is evaluated synchronously; no scheduler is required.
- **S04-R03 — Receive authorization:** Issue an authenticated, idempotent,
  rate-limited, short-lived receive grant for the server-assigned controlled room.
  The token allows join and subscribe only and denies publishing, data, room
  administration, recording, and egress.
- **S04-R04 — Transmit authorization:** Revalidate the active session/device,
  receive-grant ownership, test eligibility, expiry, rate, and one-publisher
  concurrency before granting microphone-only publication to an already-connected
  participant. Unknown/provider-degraded state fails closed.
- **S04-R05 — Release and expiry:** Release is idempotent and revokes publication
  promptly. Expiry, disconnect, logout/device revocation, account deletion, and
  receive-grant release invalidate related publishing grants. Provider failure leaves
  local authorization denied and eligible for bounded reconciliation.
- **S04-R06 — Microphone consent and lifecycle:** Add a purpose-before-permission
  mobile flow for microphone access and explicit denied, blocked/settings,
  unavailable, retry, and continue-without-audio states. No background-audio mode or
  launch-time prompt is allowed.
- **S04-R07 — Receive-ready media:** Integrate the supported LiveKit Expo development-
  build dependencies, join with microphone off, render remote audio, expose
  connecting/ready/reconnecting/degraded states, and disconnect on screen exit,
  background, logout, revocation, or unmount.
- **S04-R08 — Hold-to-talk state machine:** Provide accessible ready, authorizing,
  transmitting, receiving, busy, reconnecting, permission-denied, and error states.
  Capture begins only after server/provider authorization and stops immediately on
  release or every mandatory stop condition.
- **S04-R09 — Media privacy and security:** Restrict publication to microphone,
  prohibit raw token/secret/audio logging and storage, reject client-selected provider
  fields, keep remote-unmute disabled, and add OpenAPI, configuration, dependency,
  logging, database, and provider-grant regression tests.
- **S04-R10 — Reliability and evidence:** Test idempotency, concurrency, timeout,
  reconnect, stale grants, provider partial failure, delayed release, app lifecycle,
  permission revocation, and prior-sprint regressions. Record synthetic CI evidence;
  physical-device and live-provider claims remain explicitly pending.
- **S04-R11 — Cost controls:** Keep AWS and LiveKit unprovisioned by default, add no
  AWS resource, Redis, RDS, queue, worker, paid observability, egress, or recording,
  and document participant-minute/data ceilings and operator stop conditions.
- **S04-R12 — Compatibility and scope:** Preserve Sprint 1–3 API, authentication,
  identity, location, privacy, and cost behavior. Do not implement proximity,
  channels, maps, background audio, Bluetooth guarantees, moderation, notifications,
  recording, transcription, translation, telephony, or AI.

## Acceptance tests

| Test ID | Requirement | Procedure | Expected result |
|---|---|---|---|
| S04-T01 | S04-R01 | Run provider-contract tests with synthetic keys and injected failures while cloud configuration is absent. | Deterministic token/permission requests are produced; no network or secret is required; missing configuration fails closed. |
| S04-T02 | S04-R02 | Apply migration to empty and prior schemas; inspect rows, constraints, deletion, expiry, and logs. | Only metadata is durable; tokens, secrets, audio, transcript, and listener membership have no column or log path. |
| S04-T03 | S04-R03 | Request/replay/conflict receive grants across auth, device, rate, and over-posting cases; decode synthetic JWT claims in test. | Only caller-owned receive grants issue; claims allow join/subscribe and deny all publish/admin/data/recording actions. |
| S04-T04 | S04-R04 | Exercise eligible, duplicate, cross-device, expired, busy, degraded, and malicious transmit attempts. | Exactly one microphone-only publisher grant is active per account/device; every unknown or invalid case fails closed. |
| S04-T05 | S04-R05 | Release, expire, revoke sessions/devices/accounts, disconnect, and inject provider timeouts before/after local state changes. | Capture/publication authorization ends; retries are idempotent; local state never reauthorizes from an uncertain result. |
| S04-T06 | S04-R06 | Run mobile permission and configuration tests for unasked, granted, denied, blocked, unavailable, retry, and background transitions. | Permission is contextual and non-coercive; no background-audio permission/mode exists; every exit stops audio. |
| S04-T07 | S04-R07 | Use a fake room/event adapter to join, receive audio events, reconnect, background, exit, logout, and unmount. | Receive-ready never captures microphone; audio/session resources are cancelled deterministically on every stop path. |
| S04-T08 | S04-R08 | Drive fake-clock press/hold/release, denial, race, maximum-duration, incoming-audio, accessibility, and rapid-repeat cases. | UI and capture match the state machine; publication never precedes authorization and cannot outlive release/timeout. |
| S04-T09 | S04-R09 | Inspect OpenAPI, dependency/config allowlists, provider claims, logs/errors, database, and synthetic evidence corpus. | Zero token, secret, audio, transcript, coordinate, or unapproved provider capability leaks; only microphone publication is possible. |
| S04-T10 | S04-R10 | Run backend/mobile/security/privacy suites and load the grant service to the approved synthetic field-test scale. | Prior suites remain green; grant API p95 target is measured locally; live media NFRs remain honestly pending device evidence. |
| S04-T11 | S04-R11 | Run Terraform disabled plan and scan repository/configuration for new services and billable media features. | Zero AWS resources, no cloud calls in CI, no paid feature, and documented usage ceilings/stop rules. |
| S04-T12 | S04-R01–R12 | Complete traceability, synthetic demo, cost/privacy review, limitations, retrospective, and product-owner review. | Every requirement/test/deliverable has evidence or an explicit approved exception before Sprint 5 planning. |

## Deliverables

- **S04-D01 — Specification, readiness, and tracker:** Approve this specification and
  readiness record, then create the Sprint 4 tracker and scoped work items.
- **S04-D02 — Grant persistence and provider boundary:** Add metadata-only grant
  persistence, provider configuration, deterministic fake, and LiveKit control
  abstraction.
- **S04-D03 — Receive grant API:** Add authenticated receive-only grant creation,
  idempotency, rate limits, synthetic token-claim tests, and release.
- **S04-D04 — Transmit authorization:** Add microphone-only promotion/revocation,
  one-publisher concurrency, expiry, cascaded invalidation, and failure reconciliation.
- **S04-D05 — Mobile microphone and media foundation:** Add approved Expo/LiveKit
  native dependencies, permission flow, audio-session/room adapter, and lifecycle
  cleanup with fake-provider tests.
- **S04-D06 — Mobile PTT experience:** Add receive-ready audio, accessible hold-to-talk
  states, publish/stop ordering, maximum duration, busy/error/reconnect behavior, and
  cancellation tests.
- **S04-D07 — Security, privacy, and reliability hardening:** Add provider-claim,
  leakage, OpenAPI, lifecycle, concurrency, failure, configuration, dependency, and
  prior-sprint regression gates.
- **S04-D08 — Operations, cost controls, and evidence:** Add a PTT runbook, provider
  activation/rotation/revocation steps, usage ceilings, synthetic evidence, and
  physical-device evidence templates.
- **S04-D09 — Evidence and sprint review:** Finalize traceability, demonstrate the
  synthetic flow, record live/device exceptions truthfully, review cost/privacy/risk,
  and obtain product-owner acceptance.

## Entry criteria

- Sprint 3 review is merged and tracker #81 is closed.
- ADR-0004 remains accepted and current official LiveKit SDK/security/pricing guidance
  is reviewed.
- This specification and `sprint-4-readiness.md` are approved through issue #90.
- The implementation tracker and S04-D01–D09 issues are created from locked wording.
- Sprint 1 exceptions remain visible and block live-device/field-test claims.
- Terraform and all provider integration are disabled by default.

## Exit criteria

- S04-R01–R12 and S04-T01–T12 are implemented, traced, and reviewed.
- S04-D01–D09 are complete and the tracker is closed.
- Backend, mobile, migration, security, privacy, and disabled-IaC suites pass.
- Synthetic PTT demonstrates receive-only join, authorized microphone-only publish,
  remote receive, release, denial, expiry, and failure-closed behavior.
- No audio/token/secret/coordinate leakage or unapproved provider capability exists.
- Physical-device/cloud targets have evidence or remain named blocking exceptions; no
  simulated result is represented as field evidence.
- Final review records current and projected monthly costs before Sprint 5 planning.

## Out of scope

- proximity/radius eligibility or nearby delivery (Sprint 5);
- General, RV, or private channel membership/selection (Sprint 6);
- maps, routes, navigation, convoys, campgrounds, alerts, or emergency semantics;
- background audio, lock-screen transmission, hands-free/toggle transmission, CarPlay,
  Android Auto, or Bluetooth routing guarantees;
- recording, egress, transcription, translation, AI, telephony, SIP, agents, sound
  effects, or enhanced paid noise processing;
- Redis, RDS, queues, workers, schedulers, WebSocket control events, additional AWS
  compute, LiveKit self-hosting, load balancers, TURN infrastructure, or multi-region;
- public beta or real-user deployment.

## Cost posture

Pricing was checked on 2026-07-16 against the official LiveKit pricing, quota, and
billing pages. Prices and allowances must be rechecked immediately before activation.

| Scenario | AWS/month | LiveKit/month | Combined/month | Authorization |
|---|---:|---:|---:|---|
| Planning, implementation, CI; cloud disabled | $0 | $0 | **$0** | Proposed |
| Controlled media test on LiveKit Build; AWS disabled | $0 | $0 | **$0** | Separate activation approval required |
| Existing AWS field test + Build | $20–$23 | $0 | **$20–$23** | Separate activation approval and Sprint 1 exceptions required |
| Existing AWS field test + Build during applicable compute promotion | $8–$11 | $0 | **$8–$11** | Same gates |
| Existing AWS field test + Ship | $20–$23 | $50 minimum | **$70–$73+** | Explicit paid-plan approval required |
| Existing AWS field test + Ship during applicable compute promotion | $8–$11 | $50 minimum | **$58–$61+** | Same gate |

LiveKit Build is $0/month with hard caps of 5,000 WebRTC participant-minutes, 50 GB
of downstream data transfer, and 100 concurrent connections. It has no paid overage;
new requests fail once an allowance is exhausted. Controlled testing therefore stops
at 3,000 participant-minutes or 10 GB per calendar month, whichever comes first,
leaving substantial headroom.

LiveKit Ship starts at $50/month and currently includes 150,000 WebRTC
participant-minutes and 250 GB downstream transfer; overages are $0.0005 per
participant-minute and $0.12/GB. RoadTalk will not upgrade automatically. Approval
requires measured usage, a new cost check, and a monthly budget of at least $85 when
combined with the existing AWS field-test floor.

No recording, egress, transcription, agent, telephony, enhanced-noise, or self-hosted
feature is enabled. These would create additional meters or infrastructure and require
a new privacy, security, architecture, and cost decision.

## Security and privacy constraints

- LiveKit API secret remains server-only in an injected secret source and is never
  committed, returned, logged, stored in the database, or included in mobile builds.
- Receive tokens are short-lived, least-privilege, single-room, and single-participant.
  Production token TTL and grant TTL are separate versioned policies.
- LiveKit Cloud token revocation and participant-permission updates are defense layers;
  RoadTalk local authorization remains authoritative and fails closed.
- Remote unmute is disabled. The user action controls capture; server revocation may
  mute/unpublish but cannot silently start microphone capture.
- Audio and transcripts have no RoadTalk persistence, analytics, evidence, logging,
  moderation, backup, or export path.
- Routine logs contain only route template, result class, provider operation class,
  duration, request ID, and stable problem/termination code.
- Exact location is neither sent to LiveKit nor required in Sprint 4's controlled test
  room. Sprint 5 must add proximity eligibility without exposing coordinates.
- Participant, room, and grant references are opaque and non-identifying.
- Provider dashboard access and secret rotation require named operator procedures;
  live credentials are prohibited in CI.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Microphone captures before authorization or after release | Severe privacy harm | explicit state machine, permission confirmation before capture, capture-off-first release, max duration, lifecycle cancellation tests |
| Long-lived or over-scoped token | Unauthorized room/media access | receive-only claims, microphone-only promotion, short TTL, opaque room/identity, token decoding tests, Cloud revocation |
| Provider/local state diverges | Audio remains possible or valid users fail | local fail-closed state, idempotent release, bounded reconciliation, permission-update event handling |
| Always-connected receive sessions burn free minutes | Unexpected cap or paid-plan pressure | connect only in explicit PTT experience, disconnect on every exit/background, 3,000-minute stop ceiling |
| Native SDK breaks Expo workflow | Build/CI failure | supported development-build integration, pinned compatible versions, Expo Doctor/native configuration tests |
| Cellular/NAT/audio-route behavior differs from fakes | Unreliable field experience | named Sprint 1/device exceptions and physical-device matrix before any field claim |
| Sprint 5/6 logic leaks in | Incorrect authorization architecture | fixed server-assigned test room and explicit proximity/channel exclusions |
| Audio/token leaks through diagnostics | Privacy/security incident | closed logging fields, no bodies, synthetic canaries, provider/database/evidence scans |
| Cloud pricing changes | Budget surprise | date-stamped pricing, hard free-plan ceiling, pre-activation recheck, no automatic upgrade |
| Self-hosting appears cheaper superficially | Hidden ops and transfer cost | ADR-0004 remains controlling; require three-month measured total-cost comparison before reconsideration |

## Approval boundary

Approval in issue #90 locks this baseline and authorizes only local/GitHub CI
implementation through a newly created tracker. It does not create a LiveKit account
or project, store a live secret, activate AWS, deploy a field test, approve a paid
plan, close Sprint 1 exceptions, or authorize Sprint 5 behavior.

## Primary references

- [LiveKit pricing](https://livekit.com/pricing)
- [LiveKit quotas and limits](https://docs.livekit.io/deploy/admin/quotas-and-limits/)
- [LiveKit Cloud billing](https://docs.livekit.io/deploy/admin/billing/)
- [LiveKit Expo quickstart](https://docs.livekit.io/transport/sdk-platforms/expo/)
- [LiveKit tokens and grants](https://docs.livekit.io/home/server/generating-tokens/)
- [LiveKit participant management](https://docs.livekit.io/intro/basics/rooms-participants-tracks/participants/)
- [LiveKit camera and microphone](https://docs.livekit.io/transport/media/publish/)
