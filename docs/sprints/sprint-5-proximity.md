# Sprint 5: Proximity Engine

## Status

Proposed — awaiting product-owner approval. Sprint 4 was accepted by merged PR #108
on 2026-08-04 and authorizes Sprint 5 planning only. Coding and cloud/provider
activation remain unauthorized until this specification and readiness gate are
approved.

## Objective

Constrain each short Push-to-Talk transmission to currently eligible participants
inside one server-defined radius, using short-lived Sprint 3 location and Sprint 4
media authority without exposing coordinates, distance, direction, exact counts,
identities, or recipient membership.

## Product decisions

- Proximity is an authorization input, not a user-discovery feature. Sprint 5 does not
  add a map, nearby-person list, identity browsing, or configurable radius.
- One opaque, server-assigned controlled room remains in use. Sprint 6 owns General,
  RV, and private channel semantics.
- Both sender and recipient require active sessions/devices, current granted location
  consent, and a usable foreground location under the Sprint 3 freshness, accuracy,
  sequence, source, and plausible-movement policy.
- The radius remains server policy. The current planning default is 5,000 meters;
  clients cannot provide or infer the exact configured threshold from an API response.
- `ST_DWithin` over PostGIS `geography(Point, 4326)` with the existing GiST index is
  the authoritative inclusive boundary operation. The caller is excluded.
- A candidate must have an active receive grant in the controlled room and location
  validity extending through the proposed transmit expiry. This avoids granting a
  30-second transmission to a listener whose location will expire mid-transmission.
- A sender with no eligible recipients receives a stable semantic
  `PTT_NO_NEARBY_LISTENERS` denial. No microphone capture or provider promotion begins.
- Receive clients connect with automatic subscription disabled. The client may not
  decide which remote tracks to subscribe to.
- After publish authorization, the mobile client reports only the opaque published
  track reference. The server verifies through the provider boundary that the track
  belongs to the caller's participant and is microphone audio before any recipient is
  subscribed.
- The backend recomputes eligibility at publication time and directs the provider to
  subscribe only eligible opaque participant references. No eligible-recipient list
  is returned to either client or persisted by RoadTalk.
- The verified opaque provider track reference, proximity policy version, evaluation
  time, and semantic outcome may be attached to the transmit grant. Coordinates,
  distances, exact counts, and recipient references are never persisted as delivery
  evidence.
- Location update, pause/withdrawal, session/device/account revocation, receive-grant
  release, transmit release, and provider divergence synchronously trigger bounded
  fail-closed reconciliation for affected active transmissions. No scheduler, worker,
  WebSocket, or Redis is introduced.
- A recipient location update may change subscription during a transmission. A sender
  location update recomputes the bounded audience. Unknown, stale, partial, or
  provider-degraded state removes or denies subscription; it never preserves access
  optimistically.
- The maximum transmission duration remains 30 seconds. Sprint 5 does not add a queue,
  roaming channel, background audio/location, hands-free mode, or continuous presence.
- Local/GitHub CI implementation uses deterministic provider fakes and synthetic
  PostGIS fixtures. No live project, provider credential/call, physical-device test,
  AWS resource, payment method, or paid plan is created.

Official LiveKit documentation confirms that automatic subscription is enabled by
default, can be disabled for selective subscription, and that the Room Service API can
subscribe or unsubscribe a participant from verified track references. The design
therefore treats default-deny subscription as an explicit implementation invariant,
not an assumed provider default.

## Representative control flow

1. Authenticated clients explicitly enter the controlled PTT experience and join
   receive-ready with microphone capture off and automatic track subscription off.
2. Sprint 3 continues to maintain one short-lived current location per consenting
   foreground client.
3. On hold, the API validates the sender's session/device, receive grant, usable
   location through the maximum transmission expiry, rate, and concurrency policy.
4. A PostGIS query selects only other active receive participants whose locations are
   usable through the same expiry and satisfy the inclusive server radius.
5. If the result is empty, the API returns `PTT_NO_NEARBY_LISTENERS`; capture remains
   off and no provider permission changes.
6. Otherwise the API creates the metadata-only transmit grant and promotes the
   caller's existing participant to microphone-only publish.
7. The mobile client enables the microphone, publishes one microphone track, and
   submits its opaque track reference to the nested publication endpoint.
8. The API verifies caller ownership, source, participant, room, active grant, and
   provider state, then recomputes the eligible audience.
9. The provider boundary subscribes exactly those opaque recipient participants to the
   verified microphone track. Omitted or newly ineligible participants remain
   unsubscribed.
10. The mobile receiver renders only provider-delivered authorized audio. It never
    receives coordinates, distance, direction, exact audience size, or a recipient
    membership list.
11. Location/lifecycle changes invoke bounded reconciliation. The server unsubscribes
    newly ineligible recipients before recording a safe semantic outcome when
    possible; uncertain cleanup keeps local delivery denied and pending.
12. Release disables capture first, revokes publish authority, unsubscribes the track,
    and closes the grant idempotently. Expiry is the final safety backstop.

## API boundary

The existing resource shapes remain authoritative:

- `POST /api/v1/ptt/grants` creates a receive-only grant;
- `POST /api/v1/ptt/grants/{receive_grant_id}/transmit` authorizes a nearby-scoped
  transmission after server-side eligibility evaluation;
- `DELETE /api/v1/ptt/grants/{grant_id}` releases receive/transmit authority.

Sprint 5 proposes one nested publication handshake:

- `POST /api/v1/ptt/grants/{transmit_grant_id}/publication`

The request contains exactly one opaque `track_ref`. It accepts no account, device,
room, participant, location, radius, recipient, permission, source, policy, expiry, or
provider selector. The backend verifies that the provider reports this track as the
caller's microphone publication before applying subscriptions.

The response is metadata-only:

- transmit grant ID;
- semantic delivery state: `ready`, `no_nearby_listeners`, `reconciling`, or `ended`;
- proximity policy version;
- evaluated and expiry timestamps;
- idempotent replay indicator.

It contains no coordinates, radius, distance, direction, exact/semantic nearby count,
recipient reference/list, provider credential, or administrative payload. Stable
errors reveal only the caller's action outcome.

## Data boundary

No new location table or recipient-membership table is approved. The existing
`media_grant` transmit row may add only:

- opaque verified provider track reference;
- proximity policy version;
- eligibility evaluated timestamp;
- semantic delivery outcome;
- cleanup-pending state needed for bounded reconciliation.

The row must not contain coordinates, geohashes, radius, distance, direction, exact
counts, recipient account/device/session/grant/participant references, arrays of
members, provider payloads, audio, transcripts, or tokens. Eligibility is recomputed
from current source-of-truth rows and held only in process memory for the provider
operation.

## Requirements

- **S05-R01 — Proximity policy:** Define one versioned, server-controlled inclusive
  radius policy using Sprint 3 location usability and a 30-second maximum delivery
  window. Clients cannot select radius, precision, freshness, audience, or policy.
- **S05-R02 — Indexed eligibility:** Join current sender/candidate locations to active
  receive grants using indexed PostGIS `ST_DWithin`; exclude self, stale, inaccurate,
  withdrawn, degraded, expired, cross-room, and invalid ownership state.
- **S05-R03 — Sender authorization:** Require an authenticated active sender session,
  owned receive grant, usable location through transmit expiry, eligibility result,
  rate/concurrency allowance, and provider availability before microphone promotion.
- **S05-R04 — Recipient authorization:** Deliver only to active receive participants
  whose account/device/location/grant state is valid through the transmission window.
  Empty or unknown audiences fail closed without microphone capture.
- **S05-R05 — Selective subscription boundary:** Extend the typed provider interface
  for verified microphone-track lookup and idempotent participant subscription/
  unsubscription. Automatic subscription is disabled and deterministic fakes are used
  in CI; no live adapter or call is authorized.
- **S05-R06 — Publication handshake:** Accept only an opaque track reference, verify
  caller/room/participant/source ownership with the provider, recompute eligibility,
  and subscribe exactly the current eligible opaque participants.
- **S05-R07 — Revocation and reconciliation:** Reconcile affected active delivery on
  location replacement/withdrawal/expiry evaluation, consent/session/device/account
  revocation, receive/transmit release, disconnect, and provider partial failure.
  Local authorization fails closed before provider cleanup.
- **S05-R08 — Mobile selective receive:** Join with automatic subscription disabled,
  report only the locally published microphone track reference, render authorized
  subscribed audio, and expose accessible nearby-unavailable/ready/reconciling/error
  states without audience details.
- **S05-R09 — Privacy and security:** Prohibit coordinate, distance, direction, radius,
  exact count, recipient membership, token, secret, audio, transcript, provider
  payload, or private identifier leakage in APIs, storage, logs, metrics, evidence, or
  client state. Reject every client-selected authorization field.
- **S05-R10 — Reliability and performance:** Test boundary equality, high-latitude/
  antimeridian fixtures, races, expiry, location churn, publication replay/conflict,
  provider partial failure, and prior-sprint regressions. Measure proximity/grant p95
  at 100 accounts, 25 receivers, and 10 publishers against NFR-03's 400 ms target.
- **S05-R11 — Cost controls:** Reuse the existing API/PostgreSQL/PostGIS process and
  provider boundary. Add no AWS resource, Redis, RDS, queue, worker, scheduler,
  WebSocket, paid observability, recording, egress, or paid media feature.
- **S05-R12 — Compatibility and scope:** Preserve Sprint 1–4 authentication, identity,
  location, PTT, privacy, security, cost, and lifecycle behavior. Do not implement
  channels, blocking/muting, maps, route awareness, background behavior,
  notifications, moderation, recording, transcription, telephony, or AI.

## Acceptance tests

| Test ID | Requirement | Procedure | Expected result |
|---|---|---|---|
| S05-T01 | S05-R01 | Inspect policy/config and over-post radius/precision/freshness/audience fields. | One versioned server policy controls eligibility; client selectors are rejected without disclosing thresholds. |
| S05-T02 | S05-R02 | Run PostGIS fixtures for self/empty, inside/equal/outside radius, stale/inaccurate/withdrawn/expired/degraded, antimeridian and high latitude; inspect plan. | Only usable in-radius active receivers qualify and the GiST-indexed `ST_DWithin` path is retained. |
| S05-T03 | S05-R03 | Exercise sender auth/device/grant/location/rate/concurrency/provider/expiry combinations. | Promotion occurs only after every sender and non-empty-audience decision passes; unknown state denies. |
| S05-T04 | S05-R04 | Vary recipient session/device/location/receive-grant ownership and validity through transmit expiry. | Only recipients valid through the complete delivery window are selected; no membership is exposed or persisted. |
| S05-T05 | S05-R05 | Run provider-contract tests for auto-subscribe false, verified track lookup, subscribe/unsubscribe requests, replay and injected failures. | Requests are deterministic and default deny; no live network/secret is required; partial failure cannot broaden delivery. |
| S05-T06 | S05-R06 | Submit owned microphone, foreign, camera/data, unknown, duplicate and conflicting track references while audience state changes. | Only the caller's verified microphone track is accepted and only a recomputed eligible audience is subscribed. |
| S05-T07 | S05-R07 | Replace/withdraw/expire locations and revoke consent/session/device/account/grants during active synthetic transmission; inject delayed cleanup. | Newly ineligible delivery stops or remains locally denied/pending; bounded replay never reauthorizes uncertain state. |
| S05-T08 | S05-R08 | Drive fake room events and mobile states for no audience, ready, subscribed receive, reconciliation, denial, release, background/logout and unmount. | Client never self-selects tracks/audience; capture and subscriptions stop on every mandatory path; UI is accessible and non-disclosing. |
| S05-T09 | S05-R09 | Inspect OpenAPI, database, config, dependencies, logs/errors/metrics, mobile state and synthetic evidence with injected sensitive markers. | Zero coordinate/distance/radius/membership/token/secret/audio/transcript/provider-payload leakage and no unauthorized capability. |
| S05-T10 | S05-R10 | Run full suites and migrated-PostGIS synthetic load at 100/25/10 state with eligible/denied/reconciliation cases. | Prior suites remain green; proximity/grant p95 ≤400 ms; physical media/network NFRs remain named exceptions. |
| S05-T11 | S05-R11 | Run disabled Terraform plans and scan source/config/dependencies for services or billable features. | Zero resources/calls/new managed services and $0 current/incremental cost. |
| S05-T12 | S05-R01–R12 | Complete traceability, synthetic nearby-delivery demo, cost/privacy/risk/limitations review, retrospective, and product-owner review. | Every requirement/test/deliverable has passing evidence or an explicit approved exception before Sprint 6 planning. |

## Deliverables

- **S05-D01 — Specification, readiness, and tracker:** Approve this specification and
  readiness record, then create the Sprint 5 tracker and scoped work items.
- **S05-D02 — Proximity policy and indexed query:** Implement the versioned policy,
  usable-through-expiry rules, receive-grant join, PostGIS boundary matrix, and query-
  plan evidence.
- **S05-D03 — Nearby-scoped transmit authorization:** Integrate non-empty proximity
  eligibility into transmit creation without persisting recipient membership.
- **S05-D04 — Selective-subscription provider boundary:** Add verified microphone-track
  lookup and idempotent subscribe/unsubscribe request types, disabled implementation,
  and deterministic fake.
- **S05-D05 — Publication handshake and delivery:** Add the exact nested publication
  API, provider verification, eligibility recomputation, metadata-only persistence,
  and default-deny subscription application.
- **S05-D06 — Revocation and lifecycle reconciliation:** Reconcile active delivery on
  location, consent, authentication, grant, disconnect, expiry, and provider-failure
  paths without a scheduler or Redis.
- **S05-D07 — Mobile selective receive experience:** Disable auto-subscribe, report the
  local microphone track reference, render only provider-authorized audio, and add
  accessible non-disclosing delivery states and lifecycle cleanup.
- **S05-D08 — Security, privacy, performance, operations, and evidence:** Add contract,
  leakage, scope, dependency/config, race/failure, 100/25/10 scale, operator, and
  synthetic evidence gates with live/device exceptions.
- **S05-D09 — Evidence and sprint review:** Finalize traceability, demonstrate the
  synthetic proximity-delivery lifecycle, review cost/privacy/risk/limitations,
  complete the retrospective, and obtain product-owner acceptance.

## Entry criteria

- Sprint 4 review PR #108 is merged, issue #99 and tracker #100 are closed.
- This specification and `sprint-5-readiness.md` receive explicit product-owner
  approval before implementation issues or coding begin.
- ADR-0003 PostGIS and ADR-0004 LiveKit decisions remain accepted.
- Sprint 1 exceptions remain visible and block live-device/provider/cloud claims.
- Terraform and live provider integration remain disabled by default.

## Exit criteria

- S05-R01–R12 and S05-T01–T12 are implemented, traced, and reviewed.
- S05-D01–D09 are complete and the tracker is closed.
- Backend/PostGIS/migrations, mobile, security/privacy, disabled-IaC, dependency and
  container suites pass.
- Synthetic evidence demonstrates nearby authorization, default-deny selective
  subscription, verified publication, receive, release, denial, expiry, movement and
  failure-closed reconciliation.
- No coordinate, radius, distance, direction, exact count, recipient membership,
  token/secret/audio/transcript, or unapproved provider capability leaks.
- Physical-device/live-provider/cloud targets have evidence or remain named blocking
  exceptions; simulated results are never represented as field evidence.
- Current and projected monthly costs are reviewed before Sprint 6 planning.

## Out of scope

- user-selectable radius or exact distance/direction;
- nearby identities, lists, exact counts, maps, routes or navigation;
- General, RV, or private channel membership/selection (Sprint 6);
- block, mute, report, reputation, trust-score, moderation or abuse workflow;
- background location/audio, lock-screen transmission, hands-free/toggle mode,
  CarPlay, Android Auto or Bluetooth guarantees;
- WebSockets, Redis, queues, workers, schedulers, RDS, NAT Gateway, ALB, Fargate,
  additional AWS compute, LiveKit self-hosting or multi-region;
- recording, egress, transcription, translation, AI, telephony, SIP or agents;
- public beta, production, real-user or emergency/safety claims.

## Cost posture

Sprint 5 retains the zero-revenue policy:

Current and incremental recurring cost is **$0 AWS + $0 LiveKit per month**.

| Stage | Projected monthly cost | Authorization |
|---|---:|---|
| Planning, local code and GitHub CI | **$0** | Proposed planning; coding only after approval |
| Approved LiveKit Build device test with local backend | **$0** within RoadTalk stops | Separate test approval |
| Approved scheduled AWS window, then destroyed | **about $4–$6 in an active test month** | Separate dated approval |
| Fully destroyed inactive month | **$0** | Default |
| Intentionally retained storage/backups | **about $3–$5** | Separate retention decision |
| Always-on AWS or paid LiveKit | **Prohibited** | New architecture/cost approval |

Implementation adds no resource or dependency expected to create recurring cost.
Hard controlled-test stops remain 3,000 participant-minutes, 10 GB downstream, 25
concurrent participants, and $10 total incremental monthly cost. Crossing a stop
pauses testing; no budget, quota, payment method, plan, instance, or service may
upgrade or scale automatically.

## Privacy and threat controls

| Threat | Control | Verification |
|---|---|---|
| Sender learns who is nearby | no audience list/count/reference in request/response/log/evidence | exact schema and leakage corpus |
| Client selects radius or recipients | extra-forbidden request; server derives all policy and membership | over-posting/property tests |
| Out-of-radius audio delivery | auto-subscribe false; server-side verified selective subscription | provider-contract and boundary fixtures |
| Stale location authorizes full transmission | sender/recipient location must remain usable through grant expiry | expiry-boundary tests |
| Foreign/camera/data track is distributed | provider verification binds caller/participant/room and microphone source | malicious track-reference matrix |
| Movement/withdrawal leaves stale subscription | synchronous bounded reconciliation, local deny before cleanup | race/partial-failure tests |
| Recipient membership becomes durable | no membership table/columns; transient process list only | migration/model/evidence gate |
| Spatial query becomes unbounded | fixed maximum candidate set, GiST `ST_DWithin`, 100/25/10 p95 gate | query plan and load evidence |
| Sprint 6/12 behavior leaks in | single controlled room; explicit channel/moderation exclusions | route/schema/dependency/scope gate |
| Cost pressure causes premature services | existing process/PostGIS only; no Redis/worker/provider/cloud activation | Terraform/dependency/cost gate |

## References

- [Sprint 5 readiness](sprint-5-readiness.md)
- [Sprint 4 review](sprint-4-review.md)
- [PostGIS ADR](../adr/0003-geospatial-data-platform.md)
- [LiveKit ADR](../adr/0004-realtime-audio-platform.md)
- [LiveKit selective subscription](https://docs.livekit.io/transport/media/subscribe/)
- [LiveKit Room Service `UpdateSubscriptions`](https://docs.livekit.io/reference/other/roomservice-api/)
- [LiveKit track subscription permissions](https://docs.livekit.io/transport/media/publish/)
- [PostGIS `ST_DWithin`](https://postgis.net/documentation/tips/st-dwithin/)
