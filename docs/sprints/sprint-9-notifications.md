# Sprint 9: Notifications

## Status

Planning candidate dated 2026-08-31. Sprint 9 implementation is **not authorized** until
this specification and the companion readiness record are accepted by product-owner merge
of the planning PR. Current and incremental implementation cost ceiling remains **$0**.

## Objective

Give authenticated RoadTalk users timely, privacy-preserving awareness of relevant
RoadTalk events through an in-app notification experience and a deterministic notification
provider boundary, including a tightly constrained user-initiated urgent/emergency-alert
class, without turning RoadTalk into an emergency-dispatch, guaranteed-delivery, tracking,
marketing, or surveillance system.

## Product decisions

- Notifications are an awareness/delivery surface, **not an authorization engine**.
  Existing account/session, location consent/current-location, proximity, channel,
  Same-road and media authorization remain authoritative.
- A notification may only represent an event the recipient is already authorized to know
  about. Notification logic cannot create a wider audience or restore eligibility denied
  by an upstream rule.
- Sprint 9 notification classes are intentionally small and typed: operational/account
  notices, channel/activity notices where already authorized, and user-initiated
  **RoadTalk urgent alerts**.
- An urgent alert is a community communication aid, not emergency dispatch. RoadTalk must
  never claim that an alert reached 911, police, fire, EMS, roadside assistance, another
  driver, or any guaranteed recipient.
- Urgent-alert UI must state that delivery is not guaranteed and that users should contact
  local emergency services directly for emergencies.
- No automatic emergency detection, crash detection, medical inference, panic inference,
  emergency-services integration, public-safety feed, CAP/WEA integration, or automated
  escalation is authorized.
- No exact other-user coordinate, exact distance/bearing, heading/speed, route/corridor,
  destination, history, phone/email, private username, recovery credential, device token,
  or other authentication secret may appear in notification payloads or logs.
- If an alert needs geographic relevance, its audience is derived server-side from
  existing authorization/current-state primitives. Clients cannot submit recipient IDs,
  arbitrary radii, coordinates, routes, audience overrides, provider references, or push
  tokens.
- Notification records are bounded and purpose-limited. No durable movement history,
  notification-derived location history, behavioral profile, marketing profile, or
  cross-user engagement graph is introduced.
- Users control ordinary notification categories. Security/account notices that are
  necessary to explain account/session state may remain non-marketing and cannot be
  repurposed for engagement messaging.
- Urgent alerts are explicitly initiated, rate-limited, short-lived, idempotent, and
  clearly marked with source class and age. Retry behavior is bounded and cannot turn an
  old alert into a fresh event.
- A provider abstraction is required before any external push integration. Local/CI uses
  disabled or deterministic fake delivery only.
- APNs, FCM, Expo Push, SNS, Pinpoint, SES/SMS, Web Push services, hosted notification
  brokers, payment-info free tiers, or other external delivery systems are **not
  authorized for activation** by Sprint 9 planning.
- Browser and mobile in-app notification UX may be implemented at $0. Local OS-level
  notification behavior may be exercised only where it requires no external provider or
  recurring service.
- No background location/audio is authorized. Notification handling must not wake or
  start location/audio collection beyond OS/app behavior already separately authorized.
- Sprint 12 remains the roadmap location for full moderation/reporting/mute/spam product
  scope. Sprint 9 may implement only minimum notification-specific rate limiting,
  idempotency and abuse-resistant failure behavior required to keep alerts safe.

## Safety boundary for urgent alerts

Every urgent-alert experience must preserve these statements and behaviors:

1. **RoadTalk is not an emergency service.**
2. **Delivery is not guaranteed.** Network, app, OS, account, location, authorization or
   provider state can prevent or delay awareness.
3. **Use local emergency services directly when emergency assistance is needed.**
4. An alert is user-generated RoadTalk content, not a verified public-safety bulletin.
5. The server chooses the eligible audience from existing current authorization rules;
   the sender cannot target a person or exact location.
6. An urgent alert expires quickly and cannot silently renew itself.
7. Delivery/receipt state must not be described as proof that a person saw, understood or
   acted on the alert.

## Architecture boundary

Sprint 9 may introduce:

1. typed notification event/category/priority contracts;
2. a bounded current notification/inbox model with expiry, idempotency and read/dismiss
   state where appropriate;
3. per-account ordinary notification preferences;
4. server-side notification audience composition from existing authorized state;
5. an urgent-alert command with narrow server-selected audience, explicit TTL and rate
   limits;
6. disabled/fake notification provider adapters for deterministic CI;
7. browser and mobile in-app notification experiences;
8. optional local-device notification presentation where it does not require an external
   delivery service;
9. privacy/security/abuse/cost/performance gates and synthetic evidence.

Sprint 9 must not add emergency dispatch, automated emergency detection, arbitrary
recipient targeting, background tracking/audio, marketing campaigns, third-party
analytics, contact syncing, notification-derived user profiling, or cloud/push-provider
activation.

## Requirements

- **S09-R01 — Typed notification contract:** Define a closed set of notification classes,
  priority, expiry and public payload fields; reject over-posting and sensitive fields.
- **S09-R02 — Persistent account ownership:** Notifications/preferences belong to the
  authenticated persistent account, not a transient browser/device identity; call sign
  remains profile data and private login credentials never enter notification content.
- **S09-R03 — Preferences and state:** Provide bounded per-account ordinary notification
  preferences plus inbox read/dismiss state without creating marketing or tracking data.
- **S09-R04 — Authorization composition:** Recipients are selected server-side only after
  existing proximity/channel/route/session/account rules; notification logic may only
  narrow, never broaden, an authorized audience.
- **S09-R05 — Lifecycle and idempotency:** Notification creation/delivery is current,
  expiring, idempotent and bounded; stale/replayed/revoked/deleted state fails closed and
  does not create durable activity/location history.
- **S09-R06 — Urgent-alert safety contract:** User-initiated urgent alerts are explicitly
  labeled unverified/non-guaranteed, have short TTL/rate limits, cannot target individuals,
  and direct users to real emergency services for emergency assistance.
- **S09-R07 — Provider boundary:** Add deterministic disabled/fake notification delivery
  providers; real APNs/FCM/Expo/SNS/Pinpoint/Web Push providers remain unimplemented or
  disabled until separately approved.
- **S09-R08 — Browser experience:** Provide authenticated browser inbox/notice/urgent-alert
  UX with accessible status, expiry/source context and no unsupported browser-push claim.
- **S09-R09 — Mobile experience:** Provide equivalent mobile inbox/preferences/urgent-alert
  UX and optional local-device presentation without external push activation or new
  background location/audio permission.
- **S09-R10 — Reliability and abuse resistance:** Add bounded retries, idempotency,
  per-account/device/peer rate limits, non-enumerating failures and deletion/revocation
  handling; no always-on retry worker is required for local acceptance.
- **S09-R11 — Hardening, compatibility, performance and cost:** Add payload/log/provider/
  dependency/cost gates, synthetic scale evidence, and explicit physical/provider
  compatibility limitations under the $0 boundary.
- **S09-R12 — Evidence and review:** Produce bidirectional R/T/D/PR/evidence traceability
  and final privacy, security, accessibility, safety, provider, reliability, performance,
  compatibility, cost, risk, limitation and retrospective review.

## Acceptance tests

- **S09-T01:** Schema/API tests prove only approved notification classes/fields are
  accepted and sensitive/recipient/provider/location overrides are rejected.
- **S09-T02:** Account tests prove notifications/preferences follow the same registered
  account across sessions/devices and never expose private username/password/recovery data.
- **S09-T03:** Preference/inbox tests prove category controls, read/dismiss semantics,
  bounded retention and deletion behavior without marketing/profile fields.
- **S09-T04:** Integration tests prove notification audience composition cannot turn any
  existing proximity/channel/Same-road/session denial into a recipient.
- **S09-T05:** Lifecycle tests prove idempotency, expiry, replay denial, logout/revocation/
  deletion cleanup and no notification-derived location/history table.
- **S09-T06:** Urgent-alert tests prove explicit initiation, disclaimer/source/age, short
  TTL, rate limits, no individual/arbitrary-coordinate targeting and no delivery/read
  guarantee semantics.
- **S09-T07:** Fake/disabled provider tests are deterministic and CI rejects external
  notification-provider URLs/keys/tokens/SDK activation and spend-enabling configuration.
- **S09-T08:** Browser tests cover inbox/preferences/urgent-alert flows, accessible live
  status, expired/degraded states and persistent-account behavior.
- **S09-T09:** Mobile tests cover equivalent flows, local presentation where supported,
  permission/degraded states and absence of new background location/audio permissions.
- **S09-T10:** Reliability/abuse tests cover idempotency collisions, bounded retries,
  rate-limit dimensions, revocation/deletion races, provider failure and non-enumerating
  error behavior.
- **S09-T11:** Hardening/scale evidence exercises at least 100 accounts / 25 potential
  recipients / 10 alert publishers or a stricter matrix with a p95 target locked before
  the named run; external-provider and broad physical delivery remain explicit exceptions.
- **S09-T12:** Final review maps S09-R01–R12 to S09-T01–T12 and D01–D10 evidence and is
  accepted by product-owner merge.

## Locked delivery sequence

- **S09-D01 — Planning and readiness baseline.** This specification, readiness, cost/
  safety/provider boundary, tracker and delivery issues.
- **S09-D02 — Notification taxonomy, privacy and urgent-alert contract.** Lock public
  fields, categories, expiry, urgent semantics and prohibited targeting before persistence
  or UI.
- **S09-D03 — Notification persistence and preferences.** Bounded inbox/state/preferences,
  account ownership, deletion and retention semantics.
- **S09-D04 — Authorization and lifecycle composition.** Derive recipients only after
  existing authorization; implement expiry/idempotency/revocation/deletion behavior.
- **S09-D05 — Notification provider boundary.** Disabled/fake deterministic provider,
  bounded delivery result contract and real-provider hard-disable rules.
- **S09-D06 — Browser notifications experience.** Inbox, preferences, ordinary notices,
  urgent-alert compose/display, accessibility and degraded states.
- **S09-D07 — Mobile notifications experience.** Equivalent mobile UX plus safe local
  notification presentation where available without external provider activation.
- **S09-D08 — Urgent-alert reliability and abuse hardening.** Rate limits, idempotency,
  bounded retry/failure behavior, safety copy and no-guarantee regression tests.
- **S09-D09 — Notification hardening, scale and compatibility evidence.** Privacy/log/
  provider/dependency/cost gates, synthetic performance and explicit physical/provider
  evidence boundaries.
- **S09-D10 — Sprint evidence and review.** Traceability, final review, retrospective and
  product-owner acceptance.

Execution order is strictly D02 → D03 → D04 → D05 → D06 → D07 → D08 → D09 → D10 after
D01 planning acceptance. A later deliverable cannot bypass an unmet earlier acceptance
criterion.

## Cost and activation boundary

Approved planning/implementation ceiling: **$0 incremental recurring cost**.

Allowed for acceptance evidence:

- existing local Docker Compose/Postgres/PostGIS/media components;
- deterministic disabled/fake notification provider;
- browser/mobile in-app UX;
- local-device notification APIs when no external service/account is required;
- GitHub CI already used by the repository;
- physical-device testing on already-available hardware without paid services.

Not authorized:

- AWS resource creation or billing;
- LiveKit Cloud activation;
- APNs/FCM/Expo Push/SNS/Pinpoint/SES/SMS/Web Push provider activation or credentials;
- paid/free-tier notification provider accounts that require payment information or create
  recurring-spend exposure;
- production/public-beta deployment;
- emergency-service/public-safety integration;
- background location/audio;
- marketing/engagement notification campaigns or third-party notification analytics.

A provider being nominally free does not authorize activation, and budgets/quotas/alerts
are not automatic shutdown controls.

## Named evidence exceptions

Sprint 9 planning does not claim the following evidence exists yet:

- real APNs/FCM/Expo Push/Web Push/provider delivery, latency, quota, credential, privacy,
  terms or cost behavior;
- notification delivery while apps/devices are suspended, killed, offline, roaming or
  changing networks;
- broad physical iOS/Android/browser notification permission and presentation behavior;
- guaranteed or emergency-grade delivery, acknowledgement, response or dispatch;
- emergency-services/public-safety integration;
- multi-worker/shared rate limiting or queue durability;
- AWS deployment/billing/destroy, public-beta/production capacity or regional failover;
- background location/audio behavior;
- safety, medical, emergency, roadside-assistance or regulatory effectiveness claims.

## Approval statement

Merging the Sprint 9 planning PR means the product owner approves this specification,
companion readiness gate, locked D01–D10 order, $0 implementation policy, urgent-alert
safety boundary and named evidence exceptions. It authorizes **local/GitHub-CI Sprint 9
implementation only**. It does not authorize any external push/cloud provider, payment or
recurring spend, production/public beta, background tracking/audio, emergency-services
integration, or safety/guaranteed-delivery claim.
