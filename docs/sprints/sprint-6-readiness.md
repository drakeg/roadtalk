# Sprint 6 readiness

- Sprint: 6 — Channels
- Status: READY — approved for local/GitHub CI implementation
- Planning date: 2026-08-13
- Current and incremental cost: **$0 AWS + $0 LiveKit per month**

## Authorization boundary

The product owner approved the specification, readiness, cost policy, named evidence
boundaries, and locked S06-D01–D09 scope on 2026-08-14 through issue #129. Sprint 6
may proceed only through local development and GitHub CI in tracker #139. Approval
does not activate AWS or LiveKit, close Sprint 1 exceptions, attach a payment method,
or authorize a paid or always-on environment.

## Scope readiness

- [x] Roadmap scope is locked to General, RV, and private channel lifecycle/selection.
- [x] General and RV are the only browseable server-seeded public channels.
- [x] Private channels are invite-only and visible only to active members.
- [x] No directory, identities, member lists/counts, roles, kick/ban, messaging,
  blocking/muting, reporting, or moderation is included.
- [x] Exactly one account-wide selected channel defaults/falls back to General.
- [x] Channel authorization composes with every Sprint 5 proximity rule.
- [x] Requirements S06-R01–R12, tests S06-T01–T12, and deliverables S06-D01–D09 are
  defined with locked ordering and entry/exit criteria.
- [x] Sprint 7+ route/map/notification/moderation/AI and production behavior is out.

## Architecture readiness

### Durable channel authority

PostgreSQL remains authoritative for channel, private invite hash, membership, and
one account selection. General/RV are deterministic seeds. Private channel labels are
member-only normalized text. Invite plaintext is returned once and never stored;
verification uses a slow hash, constant-time comparison behavior, multidimensional
rate limits, and non-disclosing stable errors.

Membership is not presence. No Redis, heartbeat, WebSocket, background worker, or
membership cache is approved. A membership authorizes consideration; current selected
channel plus Sprint 5 proximity/location/grant/session state authorizes delivery.

### Provider-room decision

Each channel has an opaque server-owned provider room reference. The backend binds all
grants, microphone-track verification, and subscription requests to it. Clients never
choose or list rooms. General, RV, and private channels use the same least-privilege
provider contract and deterministic fake.

Current official LiveKit behavior supports one named room per join token and explicit
publish/subscribe grants. Rooms isolate participant state, while list/admin/recording
operations require elevated grants. Room metadata is visible to participants, so
RoadTalk stores no channel policy or membership there. Cloud-only MoveParticipant is
not used; switching disconnects and obtains fresh server authority.

### Selection and reconciliation

Selection uses an account row/version lock and idempotency fingerprint. Active
transmission blocks switching. Otherwise prior channel media authority is revoked
locally before the selection changes, provider cleanup is bounded, and mobile joins
the new room with capture and automatic subscription off. Leave, closure, invite
rotation, auth/device/account revocation, and deletion preserve fail-closed ordering.

## API, privacy, and security readiness

- [x] Catalog returns public plus caller-member private channels only.
- [x] Create/join/select/leave/rotate/close request shapes are exact and authenticated.
- [x] Client cannot submit ownership, role, type, room, participant, policy, permission,
  radius/location/audience, TTL, or provider fields.
- [x] One-time invite plaintext is restricted to create/rotation success responses.
- [x] No member identity/list/count, owner identity, invite hash/fingerprint, provider
  room/token, or proximity detail is returned.
- [x] Database/log/metric/evidence/mobile gates cover invite and label markers.
- [x] Account/channel deletion and membership withdrawal revoke media authority.
- [x] Provider claims deny room create/list/admin/record, data, camera/screen, metadata,
  ingress/egress, forwarding, SIP and agents.

## Reliability and evidence readiness

Synthetic evidence may prove schema/migrations, seeded catalog, private lifecycle,
invite hashing/rotation/rates, selection concurrency, channel-bound grants, exact
provider requests, same-channel-plus-proximity matrices, mobile transitions, bounded
reconciliation, privacy gates, multi-channel 100/25/10 p95, prior regressions, and
disabled zero-resource Terraform.

Synthetic evidence may not claim real LiveKit room isolation/token revocation/
subscription, physical-device audio or network behavior, media latency/jitter/loss,
production capacity, multi-worker correctness, AWS deployment/billing/destroy, or
automatic shutdown. S01-E01 through S01-E03 remain field-test blockers.

## Performance readiness

The migrated synthetic state remains 100 registered accounts, 25 connected receivers,
and 10 active publishers distributed across General, RV, and private channels. Report
eligible, cross-channel denied, selection/switch, invite verification, and
reconciliation p95 separately against the **400 ms** control-plane target. This does
not satisfy physical media/network NFRs.

## Cost readiness

| Decision | Status |
|---|---|
| Local planning and implementation | **$0/month** |
| GitHub CI and deterministic provider fake | **$0 RoadTalk infrastructure cost** |
| New AWS resources or managed services | None |
| Terraform | Disabled; zero resources |
| LiveKit project/credential/provider call | None |
| Redis/RDS/queue/worker/scheduler/WebSocket | None |
| Initial recurring-cost ceiling | $10/month, unchanged and not authorized |

Future references remain: separately approved LiveKit Build device test targets $0
within RoadTalk stops; a separately approved scheduled AWS window remains about $4–$6
in an active month and must be destroyed; retained storage/backups remain a separate
about $3–$5/month decision; always-on AWS or paid LiveKit remains prohibited.

Hard stops remain 3,000 participant-minutes, 10 GB downstream transfer, 25 concurrent
participants, and $10 incremental monthly cost. Alerts, budgets, and quotas are not
automatic shutdown controls or permission to spend.

## Locked implementation order

1. Approve specification/readiness and create the tracker/issues.
2. Add channel schema, General/RV seeds, catalog and selection.
3. Add private invite lifecycle and deletion behavior.
4. Bind provider/media/proximity authorization to current channel.
5. Add revoke-before-switch and lifecycle reconciliation.
6. Add mobile catalog and safe switching.
7. Add mobile private-channel lifecycle.
8. Harden privacy/security/performance/operations and assemble evidence.
9. Complete traceability, review and product-owner acceptance.

## Risk review

| Risk | Readiness control | Residual boundary |
|---|---|---|
| Private membership disclosure | caller-scoped catalog, exact schemas and no counts/listing | side-channel timing requires regression measurements |
| Invite theft/brute force | high entropy, slow hash, rate limits, one-time display, rotation | user sharing outside RoadTalk cannot be controlled |
| Cross-channel audio | channel-bound grants/rooms plus same-channel proximity predicate | live provider enforcement needs approved evidence |
| Switch race leaves authority | active-transmit denial and local revoke-before-selection | provider divergence remains fake-only |
| Provider room becomes policy source | opaque server mapping; no room metadata/listing | live adapter remains unimplemented |
| Creator deletion strands private channel | close and cascade memberships/grants | ownership transfer intentionally absent |
| User-generated label abuse | private/member-only, normalized, length-bounded, no public search | moderation is Sprint 12 and absent |
| Cost/service pressure | PostgreSQL/process-local design and exact dependency/IaC gates | scale beyond 100/25/10 requires new review |

## Approval checklist and decision

- [x] Sprint 5 review is merged and #118/#119 are closed.
- [x] Product/channel semantics and private lifecycle are explicit.
- [x] Authorization composes channel and proximity server-side.
- [x] Invite, privacy, deletion, provider, mobile, performance and scope boundaries are explicit.
- [x] Synthetic versus live/device/cloud evidence is separated.
- [x] Current/incremental cost is $0 and no activation is required.
- [x] Requirements/tests/deliverables and implementation order are complete.
- [x] Product owner approved Sprint 6 specification, readiness, cost and evidence
  boundaries through #129.
- [x] Tracker #139 and deliverable issues #130–#138 were created from the approved wording.

**READY.** Approval authorizes only local/GitHub CI Sprint 6 implementation at $0 in
locked tracker order, not live provider/cloud activation, paid services, field tests,
or Sprint 7 work.

## References

- [Sprint 6 specification](sprint-6-channels.md)
- [Sprint 6 approval issue](https://github.com/drakeg/roadtalk/issues/129)
- [Sprint 6 implementation tracker](https://github.com/drakeg/roadtalk/issues/139)
- [Sprint 5 review](sprint-5-review.md)
- [System architecture](../architecture/system-architecture.md)
- [API architecture](../architecture/api-architecture.md)
- [Data model](../architecture/data-model.md)
- [Non-functional requirements](../architecture/non-functional-requirements.md)
- [LiveKit rooms](https://docs.livekit.io/intro/basics/rooms-participants-tracks/rooms/)
- [LiveKit grants](https://docs.livekit.io/frontends/reference/tokens-grants/)
- [LiveKit Room Service](https://docs.livekit.io/reference/other/roomservice-api/)
