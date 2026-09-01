# Sprint 9 Readiness — Notifications

Date: 2026-08-31

## Gate decision

**READY FOR PRODUCT-OWNER REVIEW; NOT YET AUTHORIZED FOR IMPLEMENTATION.**

Sprint 9 coding may begin only after the planning PR containing this record and
`sprint-9-notifications.md` is merged. That merge approves only the $0 local/GitHub-CI
scope, locked D01–D10 sequence, notification privacy boundary, and urgent-alert safety
contract.

## Preconditions

- Sprint 8 is accepted by merged PR #219; issue #194 and tracker #195 are closed.
- Persistent registered-account login is available through PR #207; notifications must
  follow account ownership rather than transient browser identity.
- Existing location consent/current-location, proximity, channel, Same-road, session and
  media authorization remain authoritative.
- Sprint 8 physical compatibility gaps remain named limitations and are not erased by
  notification work.
- No external push/notification provider is selected or activated.

## Safety readiness

Urgent/emergency-labelled RoadTalk alerts are ready for local implementation only under
these constraints:

- RoadTalk is not an emergency service and does not contact emergency responders;
- delivery is not guaranteed;
- users are instructed to contact local emergency services directly when assistance is
  needed;
- alerts are user-generated/unverified, explicitly initiated, short-lived and rate-limited;
- no crash/medical/panic detection, automated escalation or emergency-services integration;
- no delivery/read receipt may be represented as proof a person saw or acted on an alert;
- clients cannot choose recipient identities, arbitrary coordinates/radii/routes or other
  targeting overrides.

The readiness gate fails if implementation requires RoadTalk to make emergency-grade,
response-time, guaranteed-delivery or verified-public-safety claims.

## Privacy readiness

Ready under these constraints:

- notification payloads use a closed/minimized contract;
- private username, password/recovery material, device token, raw other-user coordinates,
  exact distance/bearing, motion, route context, destination and history are prohibited;
- notification audience derives only from already-authorized current state;
- no notification-derived movement history, engagement graph, marketing profile or
  contact sync is introduced;
- ordinary preference and inbox state is purpose-limited and bounded;
- logs/metrics remain semantic/aggregate and exclude content or identifiers not explicitly
  approved by the notification contract.

## Security readiness

- Existing auth/session/device, recovery, location, channel, PTT, presence, dependency,
  secret, container and IaC gates remain in force.
- Create/publish APIs must use exact schemas, idempotency and authenticated server-selected
  audiences.
- Unknown/denied targets and authorization failures must not enumerate account/location/
  channel state.
- Notification-specific rate limiting must cover appropriate account/device/peer/event
  dimensions before urgent alerts are considered accepted.
- External provider credentials/URLs/SDK activation are forbidden for local/CI acceptance.

## Architecture readiness

The locked sequence deliberately separates policy from persistence, authorization,
provider and UX:

1. lock taxonomy/privacy/urgent semantics;
2. implement bounded account-owned state/preferences;
3. compose existing authorization and lifecycle;
4. lock disabled/fake provider behavior;
5. build browser/mobile UX;
6. harden urgent-alert reliability/abuse controls;
7. gather scale/compatibility evidence;
8. review.

Notification UI or provider convenience must not define the audience/safety/privacy policy
implicitly.

## Reliability readiness

- Notification creation and delivery use idempotency and explicit expiry.
- Replay/stale events fail closed; bounded retries may not refresh an old event's age/TTL.
- Logout, device/session revocation, account deletion and upstream authorization changes
  cannot silently preserve a new notification eligibility path.
- Provider failure degrades awareness; it must not alter voice/channel/proximity authority.
- No always-on queue/retry worker or shared cache is required or approved for the local
  single-worker acceptance scope.
- Delivery receipt semantics must distinguish accepted/attempted/provider-result from
  actual human reading/response.

## Provider readiness

No external push provider is approved. D05 must provide `disabled` and deterministic
`fake` providers before any later production adapter decision.

A future APNs/FCM/Expo Push/Web Push/SNS/Pinpoint or other provider activation requires a
separate dated decision covering:

- provider and supported platforms;
- account/credential/payment requirements;
- privacy/data transfer and token retention;
- terms, quotas, rate limits and acceptable-use restrictions;
- delivery semantics, retry/expiry behavior and operational ownership;
- expected recurring cost and hard disable/rollback path;
- physical-device evidence plan.

No provider's free tier is assumed to authorize production use.

## Accessibility readiness

Browser and mobile notifications must provide semantic labels, readable priority/source/
age/expiry, accessible live status, usable preferences and clear degraded/expired states.
Urgent-alert safety copy must not depend on color/icon alone. Local OS notification behavior
is supplementary; the in-app experience remains the acceptance baseline.

## Performance readiness

D09 must exercise at least 100 accounts / 25 potential recipients / 10 alert publishers or
a stricter documented matrix. A p95 threshold must be locked before the named evidence run
for server-side notification audience/event/inbox control-plane behavior. Synthetic CI
metrics must not be extrapolated to external push-provider or human response performance.

## Compatibility readiness

Local/CI implementation may exercise browser/mobile in-app notifications and local-device
presentation where supported without a provider. D09 must explicitly distinguish:

- automated UI/API evidence;
- simulator/local-device presentation evidence;
- physical iOS/Android/browser permission/presentation evidence;
- external push delivery evidence.

Any unavailable or unperformed combinations remain explicit exceptions. Sprint 8's
existing physical microphone/location gaps also remain open for release readiness.

## Cost readiness

Approved ceiling is **$0 incremental recurring cost**.

No AWS resource, LiveKit Cloud resource, APNs/FCM/Expo Push/SNS/Pinpoint/SES/SMS/Web Push
provider activation, payment-info free-tier account, hosted notification broker, paid
browser/device testing service or production deployment is authorized.

Existing local services, deterministic fixtures/fakes, browser/mobile in-app UX, local OS
notification APIs that need no external service, and GitHub CI are permitted. Any change
from $0 requires a new explicit product-owner decision before activation.

## Delivery readiness

The planning tracker must lock D01–D10 and the D02→D10 dependency order. Each delivery
issue must carry acceptance criteria from S09-R01–R12/S09-T01–T12. Sprint 10 Campgrounds
scope must not be pulled into Sprint 9.

## Named blockers and exceptions at planning time

Not blockers for local/CI implementation, but blockers for broader release/safety claims:

- real external push provider selection/credentials/delivery evidence;
- suspended/killed/offline device notification behavior;
- broad physical notification permission/presentation compatibility;
- shared multi-worker queue/rate-limit/durability behavior;
- emergency-services/public-safety integration;
- guaranteed delivery/read/response evidence;
- AWS deployment/billing/destroy and production/public-beta capacity;
- background location/audio;
- safety/medical/emergency/regulatory effectiveness claims;
- outstanding Sprint 8 physical browser/mobile microphone/location evidence gaps.

## Approval statement

Merging the Sprint 9 planning PR means the product owner approves the Sprint 9
specification, readiness gate, locked D01–D10 order, $0 implementation policy,
urgent-alert safety boundary and named exceptions. It authorizes local/GitHub-CI
implementation only. It does not authorize external push/cloud provider activation,
recurring spend, production/public beta, background tracking/audio, emergency-services
integration or safety/guaranteed-delivery claims.
