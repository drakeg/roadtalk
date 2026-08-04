# Sprint 5 readiness

- Sprint: 5 — Proximity Engine
- Status: NOT READY — awaiting product-owner approval
- Planning date: 2026-08-04
- Current and incremental cost: **$0 AWS + $0 LiveKit per month**

## Authorization boundary

Sprint 4 merge authorizes this planning record only. Sprint 5 coding begins only after
the product owner explicitly approves the specification, readiness gate, cost policy,
evidence boundary, and tracker scope. Approval does not activate AWS or LiveKit, close
Sprint 1 exceptions, add a payment method, or authorize a paid/always-on environment.

## Scope readiness

- [x] Roadmap objective is locked to radius filtering and nearby PTT delivery.
- [x] Proximity is authorization, not discovery; no identity list/map/distance output.
- [x] Sprint 5 remains separate from Sprint 6 channels and Sprint 12 moderation.
- [x] One opaque controlled room and 30-second maximum remain unchanged.
- [x] Sender and recipients require current usable Sprint 3 location and active Sprint
  4 receive authority through the delivery expiry.
- [x] Radius and all audience decisions are server-controlled.
- [x] Requirements S05-R01–R12, tests S05-T01–T12, and deliverables S05-D01–D09 are
  defined with explicit entry/exit criteria.
- [x] Background location/audio, WebSockets, Redis, workers, schedulers, channels,
  maps, moderation, recording, transcription, paid features and production are out.

## Architecture readiness

### Spatial decision

The existing PostgreSQL/PostGIS model already stores one short-lived current location
per account and uses `geography(Point, 4326)`, GiST, and `ST_DWithin`. Sprint 5 reuses
that source of truth and index. It does not add location history, geohashes, a search
index, cache, or separate proximity service.

Eligibility is inclusive at the configured radius and requires both sender and
recipient location validity through the proposed transmit expiry. This prevents
known mid-grant freshness expiry without introducing a scheduler. Location mutation
and withdrawal still invoke synchronous bounded reconciliation.

### Media delivery decision

LiveKit auto-subscription is on by default, so Sprint 5 must explicitly disable it.
Official LiveKit documentation supports selective subscription and backend
`UpdateSubscriptions` operations using participant identities and verified track
references. Sprint 5 keeps those opaque references inside the provider boundary and
never returns an audience list to mobile clients.

Publication is a two-stage fail-closed flow:

1. proximity-qualified transmit authorization promotes microphone-only publication;
2. the backend verifies the caller's reported opaque track reference and then applies
   selective subscriptions to a freshly recomputed eligible audience.

This avoids sending recipient membership to the publisher and avoids relying on a
client to enforce proximity. A deterministic provider fake proves request shape and
failure behavior; a live adapter remains separately reviewed and unactivated.

### State and reconciliation decision

No recipient-membership persistence is needed. The transmit row may retain only a
verified opaque track reference, policy/evaluation metadata, semantic outcome and
cleanup-pending state. Current eligibility is recomputed from authoritative rows.

Reconciliation is invoked by bounded application actions, not a background worker.
Unknown provider or location state fails closed. The single-worker/local-CI design is
accepted for synthetic validation; multi-worker coordination requires later measured
need, architecture review, and cost approval.

## API and privacy readiness

- [x] Existing receive/transmit/release routes remain stable.
- [x] One nested publication route has an exact, minimal request shape.
- [x] Client cannot provide account/device/room/participant/location/radius/audience/
  permission/source/policy/expiry/provider fields.
- [x] Responses contain semantic caller state only, not proximity details.
- [x] No coordinate, radius, distance, direction, exact count, recipient membership,
  token, secret, audio, transcript, or provider payload may enter storage/logs/metrics/
  evidence/mobile state.
- [x] Existing closed logging, exact OpenAPI, location and PTT privacy gates remain.
- [x] A new Sprint 5 gate will inspect schema, migrations, provider requests,
  dependencies, logs/evidence and later-sprint scope.

## Reliability and evidence readiness

Synthetic acceptance may prove:

- PostGIS boundary and query-plan behavior;
- sender/recipient authorization matrices;
- default-deny selective-subscription request shapes;
- verified publication ownership/source;
- location/grant/auth/provider reconciliation ordering;
- no membership persistence or sensitive leakage;
- proximity/grant p95 under migrated-PostGIS 100/25/10 state;
- full prior-sprint regression and zero-resource IaC behavior.

Synthetic acceptance may not claim:

- real LiveKit subscription enforcement or token revocation;
- real microphone/audio delivery or press-to-audible latency;
- physical-device permission, audio route, Bluetooth, interruption or accessibility
  gesture behavior;
- cellular/Wi-Fi transition, NAT/TURN, reconnect, jitter/loss, battery or data use;
- production capacity, multi-worker correctness, AWS deployment, billing or automatic
  shutdown.

These remain named exceptions. S01-E01 through S01-E03 continue to block field tests.

## Performance readiness

The existing NFR targets remain:

- PTT grant API p95 ≤250 ms for ordinary grant authorization;
- proximity endpoint/control decision p95 ≤400 ms at field-test scale;
- initial synthetic state: 100 registered accounts, 25 connected participants and 10
  active publishers.

Sprint 5 uses the 400 ms combined proximity/grant target and reports eligible, denied,
empty-audience and reconciliation p95 separately. This is control-plane evidence only;
it cannot satisfy physical media NFRs.

## Cost readiness

| Decision | Status |
|---|---|
| Local planning and implementation | **$0/month** |
| GitHub CI and deterministic provider fake | **$0 RoadTalk infrastructure cost** |
| New AWS resources | None |
| New managed database/cache/queue/worker | None |
| New paid dependency/provider capability | None |
| Terraform | Disabled; zero resources |
| LiveKit project/credential/provider call | None |
| Initial recurring-cost ceiling | $10/month, unchanged |

Future scenario references remain:

- approved LiveKit Build device test with local backend: target **$0** within RoadTalk
  stops;
- separately approved scheduled AWS window: about **$4–$6 in an active test month**,
  then destroy;
- destroyed inactive month: **$0**;
- intentionally retained storage/backups: about **$3–$5/month**;
- always-on AWS or paid LiveKit: prohibited without a new dated decision.

Hard stops remain 3,000 participant-minutes, 10 GB downstream, 25 concurrent
participants and $10 incremental monthly cost. Notifications and quotas are not
automatic shutdown or permission to spend.

## Dependency and implementation order

1. Approve specification/readiness and create locked tracker/issues.
2. Implement policy and indexed query before changing media authorization.
3. Integrate nearby-scoped transmit authorization with no membership persistence.
4. Extend provider boundary/fake for verified tracks and selective subscription.
5. Add publication handshake and default-deny delivery.
6. Add location/auth/grant/provider lifecycle reconciliation.
7. Update mobile selective receive and accessible semantic states.
8. Harden privacy/security/performance/operations and assemble evidence.
9. Complete traceability, review and product-owner acceptance.

## Risk review

| Risk | Readiness control | Residual boundary |
|---|---|---|
| Auto-subscribe leaks out-of-radius audio | explicit false configuration and provider/mobile regression gates | live enforcement needs approved provider evidence |
| Client lies about track | backend provider verification of room/participant/microphone source | live verification needs approved adapter test |
| Membership leaks | transient opaque list only; exact schema/storage/log/evidence gates | semantic no-audience denial reveals only none |
| Stale location remains eligible | usable-through-expiry filtering plus mutation reconciliation | device may stop reporting without field evidence; max 30-second grant bounds exposure |
| Movement race | recompute at grant/publication and bounded update reconciliation | no continuous/scheduled enforcement in approved design |
| Provider partial failure | local deny first, cleanup-pending metadata, bounded reconciliation | live provider divergence remains untested |
| Query/load regression | GiST plan assertion and 100/25/10 p95 gate | production scale not claimed |
| Premature Redis/managed service | process-local bounded work and explicit scope/cost gates | multi-worker scale deferred |
| Channels/moderation leak in | controlled room and exact exclusions | those policies remain later sprints |

## Approval checklist

- [x] Sprint 4 review is merged and tracker is closed.
- [x] Technical design is server-authoritative and default deny.
- [x] Privacy/data minimization and exact API/storage boundaries are explicit.
- [x] Synthetic versus live/device evidence is separated.
- [x] Current/incremental cost is $0 and future scenarios/stops are recorded.
- [x] No AWS/LiveKit activation or paid capability is required.
- [x] Requirements/tests/deliverables and implementation order are complete.
- [ ] Product owner approves Sprint 5 specification, readiness, cost and evidence
  boundaries.
- [ ] Tracker and implementation issues are created from the approved wording.

## Readiness decision

**NOT READY.** Planning is complete enough for product-owner review, but coding remains
blocked until explicit approval. Approval changes this record to READY and authorizes
only local/GitHub CI Sprint 5 implementation at $0. It does not authorize a live
provider adapter, project, credential/call, AWS resource, payment method, paid plan,
field test, always-on environment, or recurring spend.

## References

- [Sprint 5 specification](sprint-5-proximity.md)
- [Sprint 4 review](sprint-4-review.md)
- [System architecture](../architecture/system-architecture.md)
- [API architecture](../architecture/api-architecture.md)
- [Data model](../architecture/data-model.md)
- [Non-functional requirements](../architecture/non-functional-requirements.md)
- [LiveKit selective subscription](https://docs.livekit.io/transport/media/subscribe/)
- [LiveKit Room Service API](https://docs.livekit.io/reference/other/roomservice-api/)
- [PostGIS `ST_DWithin`](https://postgis.net/documentation/tips/st-dwithin/)
