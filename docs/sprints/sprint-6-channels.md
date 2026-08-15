# Sprint 6: Channels

## Status

Approved for local/GitHub CI implementation — product-owner approved on 2026-08-14
through issue #129. Approval covers S06-R01–R12, S06-T01–T12, S06-D01–D09, the
readiness and $0 cost policy, named evidence boundaries, and locked tracker #139.
It does not authorize provider/cloud activation, paid services, or recurring spend.

## Objective

Let an authenticated RoadTalk account select General, RV, or one caller-authorized
private channel while preserving Sprint 5 proximity eligibility, hold-to-talk safety,
metadata-only media authority, and zero disclosure of channel membership.

## Product decisions

- General and RV are server-seeded, enabled public channels. Their stable slugs and
  display labels are the only browseable channel catalog.
- A private channel is discoverable only to its active members. It never appears in a
  public search, count, presence list, nearby summary, log, metric, or evidence record.
- Private channels use a server-generated high-entropy invite secret. RoadTalk stores
  only a slow hash and a short non-secret fingerprint for idempotent diagnostics. The
  plaintext is returned once to the creator or after rotation and is never recoverable.
- Joining by invite creates an account membership without revealing the creator or
  other members. Sprint 6 has no contact lookup, invitations by email/phone, member
  directory, roles, kicking, moderation, reporting, or ownership transfer.
- The creator may rotate the invite or close the private channel. Closing revokes all
  memberships and channel-bound media authority. It exposes no member list.
- Each account has exactly one selected active channel. New accounts default to
  General. Selection is account-wide, idempotent, and server-authoritative; clients
  cannot provide a provider room, membership, role, policy, or participant selector.
- Switching or leaving first revokes channel-bound receive/transmit/publication state,
  then issues fresh authority for the selected channel. Switching is denied during an
  active local transmission; unknown provider state remains locally denied/pending.
- Every receive and transmit grant is bound to one channel ID and one opaque,
  server-derived provider room reference. Proximity eligibility adds an exact active
  same-channel membership/selection predicate before distance checks.
- LiveKit room separation is defense in depth, not the source of authorization.
  RoadTalk does not list provider rooms or participants, expose room metadata, or let
  clients choose room names.
- Channel switching reconnects with a newly issued room-bound token. Sprint 6 does not
  use LiveKit's cloud-only MoveParticipant operation and does not depend on token
  revocation claims that remain unproven without a live provider.
- Provider tokens retain receive-only join and later microphone-only promotion. They
  deny data, camera, screen share, room create/list/admin/recording, metadata mutation,
  ingress, egress, SIP, agents, and forwarding.
- Automatic subscription remains disabled. Publication still requires verified
  microphone ownership and current same-channel, in-radius recipient eligibility.
- Mobile exposes General, RV, and the caller's private channels with selected,
  unavailable, switching, and failed states. It shows no identities, membership count,
  invite fingerprint, provider room, or proximity detail.
- User-generated private-channel display text is normalized, length-bounded, private
  to members, and excluded from routine logs/metrics/evidence. It is not a public
  discovery surface or a moderation feature.
- Local/GitHub CI uses deterministic provider fakes and synthetic PostgreSQL/PostGIS
  fixtures only. No live room/project/credential/call, AWS resource, payment method,
  or paid plan is created.

Official LiveKit documentation confirms that join tokens are bound to one named room
and explicit publish/subscribe grants; rooms are isolated realtime sessions; room and
participant listing require privileged server grants; room metadata is visible to all
participants; and MoveParticipant is LiveKit Cloud-only. Sprint 6 therefore keeps
channel policy in RoadTalk, uses opaque server-derived room references, stores no
policy in provider metadata, and reconnects on selection changes.

## Representative control flow

1. An authenticated account lists the two enabled public channels plus only its active
   private memberships; the response contains semantic channel metadata only.
2. The account creates a private channel or submits an invite secret. The server
   normalizes allowed display text, creates/validates membership, hashes the secret,
   and never returns membership details.
3. Selection locks the account's current channel state. A replay returns the same
   semantic selection; a conflicting idempotency use fails closed.
4. The server denies selection while an active transmission is present, then revokes
   prior channel-bound grants before changing selection.
5. The mobile adapter disconnects the prior fake/provider room, clears authorized
   remote audio, obtains a fresh receive grant, and joins the server-derived room with
   automatic subscription and capture off.
6. Hold-to-talk authorization requires active membership/selection and applies the
   Sprint 5 proximity query only to active receivers selected into the same channel.
7. The publication handshake verifies the caller's microphone track inside the exact
   channel room and selectively subscribes only current same-channel nearby receivers.
8. Leaving a private channel falls back to General after revoking channel authority.
   Invite rotation invalidates the old secret; channel closure revokes all membership
   and media state through bounded reconciliation.
9. Background, logout, account/device/session revocation, disconnect, expiry, failure,
   and unmount preserve existing mandatory capture/subscription cleanup.

## API boundary

All routes remain under `/api/v1`:

- `GET /channels` returns enabled General/RV plus the caller's active private channels;
- `POST /channels/private` creates a private channel and returns its invite once;
- `POST /channels/private/join` accepts exactly one invite secret;
- `POST /channels/{channel_id}/select` idempotently selects an authorized channel;
- `DELETE /channels/{channel_id}/membership` leaves a private channel and selects
  General if needed;
- `POST /channels/{channel_id}/invite/rotation` rotates the creator-held invite;
- `DELETE /channels/{channel_id}` closes a creator-held private channel;
- `GET /me/channel` returns the caller's current semantic selection.

Requests accept no account/device/member/owner/role/type/provider room/participant,
radius/location/audience/policy/permission/expiry selector. Public channels cannot be
created, renamed, joined through invite, closed, or have their invite rotated.

Responses may contain channel ID, stable public slug, member-visible display label,
type, selected/enabled state, semantic timestamps/version, and a one-time private
invite on create/rotation. They contain no member identity/list/count, owner identity,
provider room/token, invite hash/fingerprint, proximity detail, or administrative
provider payload.

## Data boundary

Sprint 6 may add:

- `channel`: ID, server-owned opaque room reference, public stable slug (General/RV
  only), member-visible normalized label, type, enabled/closed state, creator account
  for private lifecycle authorization, policy version, timestamps/version;
- `channel_invite`: private channel ID, slow invite hash, non-secret fingerprint,
  created/rotated/used/revoked timestamps and version; never plaintext;
- `channel_membership`: account/channel, active/left state, joined/left timestamps and
  version; no public profile snapshot;
- `channel_selection`: one account/current channel, selected timestamp and version;
- `media_grant.channel_id`: required channel binding for new grants.

No member arrays, public member counts, messages, audio, transcripts, recordings,
presence history, precise listener locations, routes, block/mute/moderation state,
contact data, or provider payloads are approved. Account deletion cascades private
memberships/invites; creator deletion closes creator-held private channels and triggers
bounded fail-closed media reconciliation.

## Requirements

- **S06-R01 — Channel policy/catalog:** Seed exactly General and RV as enabled public
  channels; return only those plus caller-authorized private channels.
- **S06-R02 — Private-channel lifecycle:** Create, join, leave, rotate invite, and close
  private channels through exact authenticated, idempotent, failure-closed contracts.
- **S06-R03 — Invite security:** Generate high-entropy one-time-disclosed secrets, store
  only slow hashes/fingerprints, rate-limit verification, and make rotation revoke old
  invites without account or membership disclosure.
- **S06-R04 — Membership/selection integrity:** Maintain durable account membership and
  exactly one server-authoritative selected channel, defaulting/falling back to General.
- **S06-R05 — Channel-bound provider authority:** Bind grants and opaque provider rooms
  to the selected channel; deny room/admin/data/camera/recording/metadata capabilities.
- **S06-R06 — Channel-and-proximity delivery:** Require current same-channel selection
  and membership in addition to every Sprint 5 sender/recipient proximity rule.
- **S06-R07 — Switching/reconciliation:** Revoke prior channel media authority before
  switching, leave, closure, deletion, or revocation and reconnect with fresh authority.
- **S06-R08 — Mobile channel experience:** Provide accessible catalog/create/join/
  select/leave/rotate/close and switching/error states without membership disclosure.
- **S06-R09 — Privacy/security:** Prevent membership, invite, room, token, identity,
  location/proximity, display-text, secret, audio, or provider-payload leakage.
- **S06-R10 — Reliability/performance:** Test concurrency, replay/conflict, invite
  rotation races, cross-channel denial, lifecycle churn, and multi-channel state with
  100 registered accounts, 25 connected receivers, and 10 active publishers against
  the 400 ms control-plane p95 target.
- **S06-R11 — Cost controls:** Reuse the modular API, PostgreSQL/PostGIS, provider
  boundary, and client connection; add no AWS resource or paid/managed capability.
- **S06-R12 — Compatibility/scope:** Preserve Sprint 1–5 behavior and exclude presence
  service, WebSockets, Redis, maps/routes, notifications, block/mute, moderation,
  messaging, recording/transcription/telephony/AI, and background/hands-free behavior.

## Acceptance tests

| Test ID | Requirement | Procedure | Expected result |
|---|---|---|---|
| S06-T01 | S06-R01 | Inspect seeds/catalog and vary disabled/public/private/cross-account state. | Exactly enabled public plus caller-private channels appear; no membership data leaks. |
| S06-T02 | S06-R02 | Exercise create/join/leave/rotate/close auth, ownership, idempotency, over-posting and conflict paths. | Exact lifecycle works and every unauthorized/unknown state fails closed. |
| S06-T03 | S06-R03 | Inspect entropy/hash/storage/logs; brute-force rate, old/new invite, replay and marker cases. | Plaintext appears once only; hashes resist offline disclosure; rotation and limits hold. |
| S06-T04 | S06-R04 | Race selections across sessions/devices and leave/close/delete selected channels. | One valid account selection remains; General fallback and version conflicts are deterministic. |
| S06-T05 | S06-R05 | Inspect provider claims/requests for each channel and malicious room/type/permission selectors. | Room is server-derived and least privilege remains exact; no provider listing/metadata call. |
| S06-T06 | S06-R06 | Cross product channel membership/selection with proximity boundary and recipient state. | Delivery requires same current channel and proximity; cross-channel access is always denied. |
| S06-T07 | S06-R07 | Inject switching/transmit races, leave/closure/revocation, disconnect and provider failures. | Prior authority is locally revoked first; cleanup remains bounded and never broadens delivery. |
| S06-T08 | S06-R08 | Drive fake mobile catalog/create/join/select/switch/leave/close, lifecycle and accessibility states. | UI is usable/non-disclosing and capture/subscriptions stop before channel transition. |
| S06-T09 | S06-R09 | Inspect OpenAPI, database, config, dependencies, logs/errors/metrics/evidence/mobile with sensitive markers. | Zero unauthorized membership/invite/room/location/token/content leakage or capability. |
| S06-T10 | S06-R10 | Run full suites and migrated multi-channel 100/25/10 eligible/denied/switch/reconciliation load. | Prior suites pass and each control-plane p95 is ≤400 ms; media NFRs remain exceptions. |
| S06-T11 | S06-R11 | Run disabled Terraform plans and scan source/config/dependencies. | Zero resources/calls/new managed services and $0 current/incremental cost. |
| S06-T12 | S06-R01–R12 | Complete traceability, synthetic channel lifecycle, privacy/cost/risk review and product-owner acceptance. | Every item has evidence or a named approved exception before Sprint 7 planning. |

## Deliverables

- **S06-D01 — Specification, readiness, and tracker:** Approve this specification and
  readiness record, then create the locked Sprint 6 tracker/work items.
- **S06-D02 — Channel schema and public catalog:** Add channel/membership/selection
  persistence, General/RV seeds, exact catalog/current-selection APIs and migrations.
- **S06-D03 — Private channel and invite lifecycle:** Add create/join/leave/rotate/close,
  secure invite handling, limits, idempotency and deletion behavior.
- **S06-D04 — Channel-bound media authorization:** Bind grants/provider rooms to current
  selection and apply same-channel predicates to proximity authorization/publication.
- **S06-D05 — Channel switching and reconciliation:** Revoke-before-switch, reconnect,
  leave/closure/auth/deletion reconciliation, replay and partial-failure handling.
- **S06-D06 — Mobile channel catalog and switching:** Add accessible public/private
  catalog, current selection, join/select/leave and safe connection transitions.
- **S06-D07 — Mobile private-channel management:** Add create, one-time invite display,
  invite entry, rotation, closure and exact non-disclosing errors.
- **S06-D08 — Security, privacy, performance, operations, and evidence:** Add leakage,
  invite, scope, race/failure, multi-channel 100/25/10, zero-cost and synthetic gates.
- **S06-D09 — Evidence and sprint review:** Finalize traceability, demonstrate the
  synthetic lifecycle, review risks/cost/limitations, and obtain acceptance.

## Entry and exit criteria

Entry requires merged Sprint 5 review PR #127, closed #118/#119, and explicit approval
of this specification, readiness, $0 cost policy, named exceptions, and tracker scope.
Those conditions were satisfied on 2026-08-14 through approval issue #129 and locked
tracker #139.

Exit requires S06-R01–R12, S06-T01–T12, and S06-D01–D09 fully traced; complete green
backend/PostGIS/migration/mobile/security/disabled-IaC suites; synthetic General/RV/
private lifecycle and cross-channel denial evidence; and honest field exceptions.

## Cost posture and out of scope

Current and incremental recurring cost is **$0 AWS + $0 LiveKit per month**. Terraform
remains disabled and plans zero resources. Hard stops remain 3,000 participant-minutes,
10 GB downstream, 25 concurrent participants, and $10 incremental monthly cost; these
are ceilings, not authorization to spend or automatic shutdown controls.

Out of scope: public channel creation, channel search/directories/member counts, roles/
admins/kicking, messaging, blocking/muting/reporting/moderation, presence/WebSockets,
maps/routes/notifications, background audio/location, hands-free mode, recording,
egress, transcription, translation, telephony/SIP, agents/AI, self-hosting, Redis/RDS,
queues/workers/schedulers, new AWS resources, production/public beta, and safety or
emergency-service claims.

## References

- [Sprint 6 readiness](sprint-6-readiness.md)
- [Sprint 6 approval issue](https://github.com/drakeg/roadtalk/issues/129)
- [Sprint 6 implementation tracker](https://github.com/drakeg/roadtalk/issues/139)
- [Sprint 5 review](sprint-5-review.md)
- [API architecture](../architecture/api-architecture.md)
- [Data model](../architecture/data-model.md)
- [LiveKit rooms](https://docs.livekit.io/intro/basics/rooms-participants-tracks/rooms/)
- [LiveKit access grants](https://docs.livekit.io/frontends/reference/tokens-grants/)
- [LiveKit Room Service](https://docs.livekit.io/reference/other/roomservice-api/)
- [LiveKit room metadata](https://docs.livekit.io/home/client/state/room-metadata/)
