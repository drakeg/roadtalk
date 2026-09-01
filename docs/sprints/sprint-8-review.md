# Sprint 8 Review — Map Experience

## Decision

**Approved upon merge of the S08-D10 review pull request.** Merge is the product-owner
acceptance event for Sprint 8 only. Until that merge, this document is a review candidate
and issue #194 / tracker #195 remain open.

Acceptance means RoadTalk has completed the approved **local/GitHub-CI Map Experience
milestone with limited named physical compatibility evidence**. It does not authorize
Sprint 9 coding, a production/public beta, AWS or LiveKit Cloud activation, a production
map/tile/geocoding/routing provider, payment method, paid/free-tier provider account,
recurring spend, background location/audio, navigation, trip history, emergency tracking,
or safety/driver-distraction claims.

Sprint 9 requires its own dated planning/readiness/product-owner approval.

## Scope delivered

Sprint 8 delivered the locked D01–D10 sequence:

- privacy-preserving nearby presence using fixed 2 km cells, a 3-account minimum, bounded
  visible cells and coarse density buckets;
- current-only lifecycle derived from accepted foreground location and existing consent,
  account/session/device state;
- explicit proof that map/presence awareness cannot broaden communication authorization;
- deterministic disabled/fake map-provider boundary with no public provider/network call;
- browser awareness surface with own foreground location, coarse presence, diagnostics
  and navigation;
- mobile awareness surface using the existing foreground-only location lifecycle;
- accessible text-equivalent awareness and degraded states that avoid false precision;
- persistent registered-account browser login introduced after physical testing exposed
  the inadequacy of anonymous browser identity rotation for returning users;
- a physical compatibility matrix that records actual MacBook microphone/location success
  and preserves every unperformed hardware/browser row as an exception;
- privacy/provider/license/cost hardening plus a 100/25/10 synthetic PostGIS presence
  matrix;
- final bidirectional traceability and this review.

Detailed mapping is in `docs/sprints/sprint-8-traceability.md`. Physical compatibility
is recorded in `docs/sprints/sprint-8-d08-physical-compatibility.md`; D09 hardening and
performance evidence is in `docs/evidence/sprint-8/README.md`.

## Requirement and acceptance result

**S08-R01–S08-R12 and S08-T01–S08-T12 are accepted only within the documented local/CI
scope and named exceptions.** The final acceptance depends on merge of this review PR;
that merge completes S08-T12/S08-D10 and permits issue #194 and tracker #195 to close.

The core invariant remains: the map is an awareness surface, not an authorization engine.
Existing location consent/current-location, proximity, channel, session/grant and
Same-road authorization remain authoritative. Presence can never turn a prior denial
into an eligible communication path.

## Privacy review

Accepted privacy properties:

- the current user's own accepted foreground location may be rendered precisely only for
  their own orientation;
- other-user presence exposes only approximate 2 km cell centers and `few` / `several` /
  `many` density labels after the minimum anonymity threshold is met;
- one/two-account cells are suppressed; conflicting samples for one account fail closed;
- another user's raw coordinate, exact count, account/device identity, call sign,
  distance/bearing, heading/speed, route/corridor/direction, destination and history are
  excluded from the client contract;
- presence is current-only and no history/breadcrumb/trail table is introduced;
- stale location, consent withdrawal, inactive account/session/device state and viewer
  self-presence fail closed;
- browser/mobile degraded states hide stale nearby activity rather than imply precision;
- usernames introduced by registered login are private authentication metadata and are
  not part of public presence/identity payloads.

Residual privacy risk is concentrated in future real-provider activation and physical
field behavior; neither is inferred from Sprint 8 synthetic evidence.

## Security review

Normal CI plus Sprint 7 and Sprint 8 hardening workflows preserve authentication,
consent, PostGIS, channels/grants, dependency, secret, container and zero-resource IaC
gates.

Sprint 8 additionally enforces:

- exact selector/schema rejection for nearby presence;
- forbidden-field leakage checks;
- fixed sparse-policy parameters;
- lifecycle requirements for current location and active source-device sessions;
- disabled/fake-only map provider configuration;
- rejection of external map/network credential/provider markers and spend-enabling
  dependencies;
- persistent registered-account login using versioned salted slow password hashes with
  non-enumerating login failure behavior.

No background worker, tracking service, public tile client, hosted identity provider or
new cloud queue/cache was added.

## Accessibility review

D07 provides text-equivalent awareness so essential map state is not visual-only.
Browser controls use keyboard/focus/semantic status treatment and mobile controls provide
labels/hints; visual coarse markers are not duplicated into confusing accessibility
announcements. Degraded/unavailable states explicitly communicate that nearby activity is
not shown.

Automated accessibility tests are regression evidence. Broad physical assistive-technology
and gesture testing remains unperformed and is not implied by acceptance.

## Provider and licensing review

No production map provider or map dataset was selected, activated, downloaded or
distributed. Sprint 8 therefore does not claim that any future provider/dataset license
has been satisfied.

Before production map/provider activation, a separate dated decision must record the
selected provider/dataset and its license/attribution obligations, privacy/data transfer,
caching/offline/redistribution terms, quotas/rates, credentials, expected recurring cost,
update ownership and rollback/disable plan. A public/free endpoint is not assumed to be
free production infrastructure.

## Reliability and lifecycle review

Accepted synthetic behavior covers stale/expired current location, consent withdrawal,
logout/session/device revocation, inactive accounts, sparse populations, conflicting
samples, malformed client responses/provider results and degraded client states.

Nearby presence is derived at read time from existing current state rather than maintained
by an always-on presence/history worker. Provider failure cannot broaden communication
eligibility; degraded awareness fails closed.

The persistent account correction was an important reliability/product finding. Physical
browser testing showed permission acquisition worked but exposed that an anonymous-only
identity could strand an existing call sign. PRs #201/#202 improved recovery diagnostics,
and #207 established registered username/password login while preserving the same account
profile/call sign during promotion.

## Performance review

D09 uses a migrated disposable PostGIS matrix of **100 registered accounts / 25 presence
viewers / 10 active publishers**, with five repeated refresh rounds.

Authoritative D09 evidence recorded:

- current-presence lookup/aggregation p95: **3.44 ms**;
- repeated refresh p95: **2.30 ms**;
- locked target: **400 ms p95** for both.

The final D09 head passed normal CI #401, Sprint 7 hardening #73, and Sprint 8 hardening
#6. These measurements are synthetic CI/PostGIS control-plane evidence only. They do not
establish production map-provider latency, moving-device GPS behavior, media/network
latency, cellular/Wi-Fi handoff or public production capacity.

## Physical compatibility review

The D08 evidence matrix records one genuine physical observation: on a physical MacBook,
pressing **Start RoadTalk** resulted in both microphone and foreground location being
reported enabled. The subsequent error was the independent browser-session/account defect
that ultimately led to persistent registered login.

The following remain explicitly unperformed/unavailable and are not converted to PASS by
CI:

- exact MacBook browser/version and separate localhost versus HTTPS-LAN execution;
- physical microphone denial/recovery and location denial/recovery;
- physical receive/speaker path;
- physical iPhone browser behavior;
- physical native iPhone microphone/location behavior;
- Android physical-device behavior;
- additional desktop OS/browser combinations;
- broad Bluetooth/interruption/battery/data/accessibility-gesture behavior.

This review accepts those as named evidence gaps, not as compatibility claims.

## Cost and infrastructure review

Approved current and incremental cost remains **$0 AWS + $0 LiveKit Cloud + $0
map/location provider per month**.

Sprint 8 uses existing local Docker/PostGIS/media development boundaries, deterministic
fixtures/fakes, available physical hardware and GitHub CI. Terraform remains disabled and
no map/provider account, payment method, AWS resource or LiveKit Cloud resource was
activated.

Budgets, alerts, quotas, free-tier labels and CI checks are not automatic shutdown
controls and do not authorize spend. Any future provider/cloud activation requires an
explicit dated cost/rollback decision.

## Compatibility and regression review

D09 final evidence kept backend/database/migration, mobile, dependency, privacy, IaC,
container and prior Sprint hardening gates green. The D06 implementation initially merged
with three stale exact-equality mobile test expectations after own coordinates were added
to the local-only snapshot; follow-up PRs #210/#211 corrected only those expectations.
That incident reinforces that merged feature behavior is not considered accepted merely
because the implementation appears correct—the final review relies on named green evidence.

Sprint 8 does not retroactively widen Sprints 1–7 authorization, cloud, provider, field or
safety boundaries.

## Named limitations and evidence exceptions

The following are **not performed/approved** by Sprint 8 acceptance:

- production map/tile/geocoding/routing provider selection, licensing compliance,
  attribution placement, quotas, caching/offline behavior, availability or latency;
- production map/road dataset selection, distribution, geographic coverage or update
  operations;
- broad physical browser/mobile microphone, speaker, Bluetooth, GPS, permission,
  interruption, battery and data behavior beyond the one documented MacBook observation;
- background location/audio;
- live LiveKit Cloud media, NAT/TURN/cellular handoff or multi-region behavior;
- AWS deployment, billing, destroy, production/public beta or multi-worker capacity;
- navigation, destination/address search, ETA, itinerary, trip history or geofencing;
- driver-distraction, emergency, hands-free, regulatory or safety claims.

Any future release/readiness decision must carry these forward until separately evidenced
or explicitly accepted under a later approved plan.

## Risk review

Key remaining risks:

1. Real map/provider terms, attribution, privacy transfer, latency, quota and cost may
   differ materially from the deterministic fake boundary.
2. Physical browser/mobile permission and hardware behavior varies by OS, browser, origin,
   device and peripheral and remains lightly evidenced.
3. Synthetic presence timings do not model moving GPS, external provider traffic, media
   transport or public production load.
4. Coarse cells reduce precision but do not eliminate every contextual re-identification
   risk in very sparse or externally observable scenarios; the 3-account threshold must
   remain fail-closed and should be re-evaluated before public deployment.
5. Persistent account login improves call-sign continuity but introduces credential
   lifecycle/support expectations that need later release-oriented recovery UX review.

Mitigation is to preserve current fail-closed/provider-disabled boundaries and require
separate provider/device/live/field/release evidence before widening claims.

## Retrospective

What worked:

- locking the privacy contract before provider/UI work kept the anonymity invariant clear;
- composing presence after existing authorization avoided a second eligibility engine;
- deterministic provider fixtures and PostGIS scale tests gave useful evidence at $0;
- physical testing caught a product-account flaw that automated map tests would not have
  revealed;
- explicit D08 `NOT PERFORMED` rows prevented CI from being mistaken for physical support;
- dedicated hardening gates preserved provider/cost/privacy boundaries through later work.

What needs improvement:

- D06 was merged while its final normal CI still contained stale snapshot tests; future
  PR merge discipline should require all authoritative checks green before merge;
- browser account/session behavior should have been modeled as persistent login earlier,
  rather than relying on anonymous identity recovery once call signs became durable user
  profiles;
- physical compatibility evidence remains much thinner than the release-readiness goal;
  representative iPhone/Android and denial/recovery tests should be planned explicitly
  before a field/public beta claim;
- future Sprint trackers should distinguish implementation completion from final named
  evidence completion when a deliverable spans feature code plus evidence repairs.

## Closure and next-step boundary

Upon merge of the S08-D10 review PR:

- issue #194 may close as completed;
- tracker #195 may mark S08-D10 complete and close;
- Sprint 8 is accepted as the documented local/CI milestone with the named physical
  compatibility observation and explicit evidence gaps;
- Sprint 9 planning may begin, but **Sprint 9 coding remains unauthorized until a new
  Sprint 9 specification/readiness/cost boundary is explicitly approved**.

No part of this review authorizes a production map/provider/dataset, AWS, LiveKit Cloud,
paid/recurring services, production/public beta, background tracking, navigation or
physical-field/safety claims.
