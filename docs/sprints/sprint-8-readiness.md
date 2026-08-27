# Sprint 8 Readiness — Map Experience

Date: 2026-08-26

## Gate decision

**READY FOR PRODUCT-OWNER REVIEW; NOT YET AUTHORIZED FOR IMPLEMENTATION.**

Sprint 8 coding may begin only after the planning PR containing this record and `sprint-8-map-experience.md` is merged. That merge approves only the $0 local/GitHub-CI implementation scope and locked delivery sequence.

## Preconditions

- Sprint 7 is accepted and tracker #173 is closed.
- Nearby remains the default communication mode; Same road remains an explicit narrowing filter.
- Existing location consent/current-location, PostGIS proximity, channel/session/grant, and route authorization remain authoritative.
- Broad physical-system microphone/location compatibility remains a known release blocker and is explicitly included as D08 evidence work.
- No production map/tile provider or dataset has been selected or activated.

## Privacy readiness

Ready under these constraints:

- own foreground location may be rendered for the authenticated user;
- another user's raw coordinate, exact distance/bearing, heading/speed, route/corridor/direction, destination, history, or identity-location association is prohibited;
- D02 must lock a deterministic coarse-presence and sparse-population policy before UI implementation;
- presence is current-only and short-lived;
- map/presence cannot broaden communication authorization;
- no background tracking, map history, breadcrumb, replay, or route history is introduced.

Privacy gate fails closed if D02 cannot demonstrate a representation that avoids near-unique user localization.

## Security readiness

- Existing authenticated API, consent, session/device, PostGIS, channel/grant, route-mode, dependency, secret, IaC, and container gates remain in force.
- Presence endpoints must use exact schemas and reject client attempts to select another user, coordinate, radius override, map cell, route, provider, or audience.
- Real/public map provider configuration must be hard-disabled for local/CI acceptance.
- Logs/metrics must remain aggregate/semantic and must not contain other-user coordinates, presence-cell membership tied to identity, provider payloads, or eligibility reasons.

## Architecture readiness

The delivery order deliberately separates privacy policy from provider and UI work:

1. lock coarse/sparse presence semantics;
2. lock deterministic provider boundary;
3. compose lifecycle and existing authorization;
4. build browser/mobile UI;
5. complete accessibility/degraded behavior;
6. gather physical compatibility evidence;
7. harden/scale;
8. review.

This prevents a map library or UI convenience from defining privacy policy implicitly.

## Accessibility readiness

A visual map alone is not acceptable. Sprint 8 requires a text-equivalent awareness summary, semantic controls/status, keyboard operability on browser controls, and screen-reader meaningful state. Exact accessibility acceptance is delivered in D07 and reviewed again in D10.

## Reliability readiness

- Presence derives only from accepted, fresh foreground location state.
- Stale/missing/denied location produces a degraded/unavailable state rather than fabricated precision.
- Sparse-population protection fails closed.
- Provider/tile failure must not affect existing voice authorization or Nearby/Same-road eligibility.
- No tight-loop/background refresh service is approved.
- Refresh/reconciliation must be bounded and cancelable.

## Performance readiness

D09 must exercise at least the accepted Sprint 7 synthetic population of 100 accounts / 25 receivers / 10 publishers or a stricter documented matrix. Presence lookup/aggregation/refresh must have an explicit p95 threshold chosen before the named evidence run, and the review must not extrapolate synthetic CI timings to production map/provider/network capacity.

## Licensing/provider readiness

No production provider is approved. Before any future public/hosted map/tile or production dataset activation, a dated decision must document:

- provider/dataset and geographic scope;
- license and required attribution placement;
- derivative/share-alike obligations where applicable;
- terms, privacy, retention, caching/offline rules, quotas/rate limits;
- update/version process and operational owner;
- expected recurring cost, hard spend controls, rollback, and exit path.

Public OpenStreetMap tile services or similar community endpoints must not be assumed to be free production infrastructure.

## Compatibility readiness

D08 must define a named representative physical-system matrix before claiming broad compatibility. At minimum it should record, where available without paid services:

- desktop browser/OS and secure-origin mode;
- microphone acquisition and denial/recovery;
- receive/speaker path where feasible;
- foreground geolocation acquisition and denial/recovery;
- local `localhost` versus HTTPS LAN behavior;
- mobile simulator/physical-device foreground location and microphone behavior where available;
- unsupported, blocked, or unperformed combinations as explicit exceptions.

Passing unit/CI tests alone cannot close this gate.

## Cost readiness

Approved ceiling is **$0 incremental recurring cost**.

No AWS, LiveKit Cloud, hosted map/tile/geocoding/routing/traffic provider, paid/free-tier account requiring payment information, production dataset distribution, or recurring service is authorized. Existing local Docker/PostGIS/media development components, deterministic fixtures/static assets, and GitHub CI are permitted.

Any change from $0 requires a new explicit product-owner decision before activation.

## Delivery readiness

The planning tracker must lock D01–D10 and dependency order. Each delivery issue must include acceptance criteria derived from the corresponding S08 requirements/tests. No scope may be pulled forward from Sprint 9+.

## Named blockers and exceptions at planning time

Not blockers for local/CI implementation, but blockers for broader claims/activation:

- production map/tile provider and licensing evidence;
- real map/provider latency/availability/quota evidence;
- broad physical microphone/location/device compatibility until D08;
- live cloud media/network evidence;
- AWS deployment/billing/destroy evidence;
- public-beta/production capacity and operational evidence;
- safety/navigation/emergency/regulatory validation.

## Approval statement

Merging the Sprint 8 planning PR means the product owner approves the Sprint 8 specification, readiness gate, locked D01–D10 order, $0 implementation policy, and named evidence exceptions. It authorizes local/GitHub-CI implementation only. It does not authorize provider/cloud activation, recurring spend, production/public beta, background tracking, or safety/navigation claims.