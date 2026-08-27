# Sprint 7 Review — Route Awareness

## Decision

**Approved upon merge of the S07-D09 review pull request.** Merge is the product-owner
acceptance event for Sprint 7 only. Until that merge, this document is a review
candidate and issue #172/tracker #173 remain open.

Acceptance means RoadTalk has completed the approved **local/GitHub-CI synthetic Route
Awareness milestone** with Nearby preserved as default and explicit Same-road filtering
implemented behind the accepted privacy/security/provider boundaries.

This review **does not authorize Sprint 8 coding**, a production/public beta, a real
routing provider or road dataset, AWS/LiveKit Cloud resources, a payment method, paid
plan, external route request, recurring spend, or any field/safety/navigation claim.
Sprint 8 requires its own dated planning/readiness/product-owner approval.

## Scope delivered

Sprint 7 delivered the locked D01–D09 sequence:

- versioned authenticated Nearby/Same-road account mode with Nearby default;
- typed deterministic route-context provider boundary with real providers disabled;
- one minimized current route-context row keyed to the accepted foreground location;
- Same-road composition after existing proximity/channel/session/grant authorization;
- deterministic keyed-corridor/coarse-direction compatibility that fails closed;
- bounded route-context/media cleanup, semantic operations signals and runbook;
- mobile/browser generic mode/matching/unavailable experience without route disclosure;
- browser release hardening for secure-context diagnostics, microphone preflight,
  bounded location fallback and Operations/Web Radio/Audience navigation;
- route-awareness privacy/provider/licensing/cost gates and the synthetic 100/25/10
  PostGIS control-plane matrix;
- final bidirectional traceability and this review.

Authoritative detailed mapping is in `docs/sprints/sprint-7-traceability.md`. D08 hardening
and performance evidence is in `docs/evidence/sprint-7/README.md`.

## Requirement and acceptance result

**S07-R01–S07-R12 and S07-T01–S07-T12 are accepted within the documented synthetic
scope and named exceptions.** The final acceptance depends on merge of this review PR;
that merge completes S07-T12/S07-D09 and permits issue #172 and tracker #173 to close.

The implementation preserves the central authorization invariant: Same-road is never a
new eligibility source. Existing Sprint 5 PostGIS proximity and Sprint 6
channel/session/grant authorization determines candidates first; route context can only
remove recipients. Nearby behavior remains the default path.

## Privacy review

Accepted privacy properties:

- clients select only Nearby or Same road and cannot submit road, corridor, provider,
  direction, confidence, TTL, destination, route or audience overrides;
- no client-callable route-matching endpoint exists;
- server route matching uses only the already-approved current foreground location
  sample plus minimized quality/motion metadata;
- durable context contains one keyed/non-portable corridor digest, coarse direction,
  confidence, source location version, provider/policy version and short timestamps;
- no road name, snapped point, trace, geometry, route, destination, itinerary or raw
  provider payload is persisted or returned;
- logs/metrics expose semantic/aggregate state only and discard route, identity,
  provider and eligibility details;
- missing, expired, ambiguous, mismatched, stationary/unknown or failed context denies
  Same-road rather than silently widening the audience;
- pause, consent withdrawal, logout, deletion, revocation and accepted-location changes
  invalidate/remove context and media authority through bounded lifecycle paths.

Residual privacy risk is dominated by future real-provider/dataset activation and
physical-device behavior. Those are explicitly outside this acceptance and require a
new decision/evidence record.

## Security review

Normal CI and the dedicated Sprint 7 hardening workflow keep the existing authentication,
location consent, PostGIS, channel/grant, dependency, secret, IaC and container gates in
force. Sprint 7 adds explicit provider/config/schema/client/log/evidence boundary checks.

The real routing provider remains hard-disabled: configuration accepts only `disabled`
or `fake`; no provider URL/key/secret/token is added; no OSRM/OSM network implementation
or road dataset is present. Same-road failures deny delivery without exposing the denial
reason. Automatic subscription remains disabled.

No new always-on worker, Redis/WebSocket service, cloud queue, routing container or
external network dependency was introduced.

## Licensing review

No production routing dataset was selected, downloaded, distributed or activated.
OSRM remains only a candidate adapter and no public OSRM/OSM endpoint is treated as free
production infrastructure.

Before any future OpenStreetMap-derived dataset activation, the architecture/product
record must document ODbL attribution, applicable share-alike obligations for a derived
database, dataset source/version/geographic scope/update process, attribution placement,
provider terms/rates/privacy/retention, operating responsibility and recurring cost.
Sprint 7 records those obligations but does not claim compliance for an unselected
production dataset.

## Reliability and failure review

Accepted synthetic behavior covers provider timeout/malformed/low-confidence results,
source-location mismatch/freshness/order/concurrency, corridor/direction mismatch,
missing/expired context, route-mode transitions and bounded cleanup/reconciliation.
Nearby users remain independent of route-provider availability; Same-road users fail
closed when route context cannot be trusted.

The Operations path exposes aggregate fresh/expired route contexts and reconciling media
grants without sensitive details. There is no tight-loop/background retry service;
operator/request-driven cleanup remains explicitly bounded.

## Performance review

The D08 migrated PostGIS matrix models **100 accounts / 25 receivers / 10 publishers**
and exercises Nearby, matching Same-road, corridor/direction denial, zero-recipient and
publication/subscription reconciliation control-plane paths.

Named authoritative run `33035376277` recorded:

- Nearby eligible lookup p95: **40.71 ms**;
- Same-road eligible lookup p95: **24.03 ms**;
- Same-road zero-recipient denial p95: **18.97 ms**;
- reconciliation p95: **160.94 ms**;
- accepted control-plane threshold: **400 ms p95**.

Final D08 head also passed dedicated hardening run `33035637402` and normal CI run
`33035637450`. These measurements are synthetic CI/PostGIS control-plane evidence only;
they do not establish real routing-provider, WebRTC media, device, network or production
capacity performance.

## Cost and infrastructure review

Approved current and incremental cost: **$0 AWS + $0 LiveKit Cloud + $0 routing provider
per month**.

Sprint 7 uses existing local Docker Compose/PostGIS/media boundaries, deterministic
fixtures/fakes and GitHub CI. Terraform remains disabled and validation creates no
resources. No external route request, road dataset download, AWS resource, LiveKit Cloud
resource, provider credential/account/payment method or paid plan was authorized.

Alerts, budgets, CI checks, quotas and cost ceilings are **not automatic shutdown
controls** and do not authorize spend. Any future provider/cloud activation requires
explicit product-owner approval with a dated cost/rollback decision.

## Compatibility and regression review

The final D08 normal CI kept formatting, Ruff, mypy, migrations/schema drift, full
backend/PostGIS tests, Sprint 4/5/6 scale checks, downgrade/upgrade, Expo Doctor/mobile
typecheck/tests, dependency audits, prior Sprint privacy/scope/review gates, Terraform
validation, Trivy filesystem/container scans and container build green.

Sprint 7 does not retroactively alter the accepted Sprints 1–6 boundaries. Existing
Sprint 1 field blockers S01-E01 through S01-E03 remain field-test blockers.

## Named limitations and evidence exceptions

The following were **not performed** and are not implied by Sprint 7 acceptance:

- real-road/provider match quality, ambiguity rate, map completeness/freshness, quotas,
  provider availability or provider latency;
- selection/distribution/licensing compliance of a real production road dataset;
- physical-device GPS quality, battery/data behavior, OS permission variation or
  background location behavior;
- broad cross-browser/physical-system microphone/speaker, Bluetooth, interruption and
  accessibility-gesture validation;
- live LiveKit media latency/jitter/loss, NAT/TURN, cellular/Wi-Fi handoff, live
  subscription revocation or multi-party road scenarios;
- AWS deployment/billing/destroy, production/public beta, multi-worker or regional scale;
- driver-distraction, emergency, safety, navigation, hands-free or regulatory claims.

PR #183 improves browser diagnostics/preflight/fallback and is covered by automated
regression tests, but it does not close the physical cross-system microphone/location
exception. That remains release/field evidence to gather before claiming broad browser
hardware compatibility.

## Risk review

Key remaining risks are:

1. A future real provider/dataset may produce different ambiguity, latency, privacy,
   licensing and cost characteristics than the deterministic fake.
2. Browser and mobile permission/hardware behavior can vary materially by origin,
   browser, OS and physical device even with the hardened client flow.
3. Synthetic control-plane timings do not include real route-provider or media/network
   latency and must not be extrapolated to production capacity.
4. Same-road is a coarse privacy-preserving approximation; corridor normalization and
   direction policy will need field evaluation before any safety-sensitive use.

Mitigation is to preserve the current hard-disable/fail-closed boundaries and require
separate provider/dataset/device/live/field evidence before widening claims or scope.

## Retrospective

What worked:

- strict delivery ordering kept the route-mode/provider/context/authorization layers
  independently reviewable;
- composing Same-road after existing authorization preserved a clear security invariant;
- fake-provider and PostGIS synthetic evidence enabled meaningful testing at $0;
- CI gates caught real regressions, dependency drift and missing evidence rather than
  allowing the review to become a paperwork exercise.

What needs improvement:

- D08 was initially treated as complete after the browser-hardening PR even though the
  locked issue still required route-specific leakage/performance/licensing evidence;
  reopening #171 and adding PR #184 corrected that before final Sprint acceptance;
- browser microphone/location compatibility remains an important physical-system release
  risk and should receive explicit field evidence rather than being inferred from unit/CI
  coverage;
- future Sprint trackers should make multi-PR deliverables/evidence checkpoints more
  explicit so feature hardening cannot be mistaken for full acceptance evidence.

## Closure and next-step boundary

Upon merge of the S07-D09 review PR:

- issue #172 may close as completed;
- tracker #173 may mark S07-D09 complete and close;
- Sprint 7 is accepted as the documented local/CI synthetic milestone;
- Sprint 8 planning may begin, but **Sprint 8 coding remains unauthorized until a new
  Sprint 8 specification/readiness/cost boundary is explicitly approved**.

No part of this review authorizes activation of a real route provider/dataset, AWS,
LiveKit Cloud, paid/recurring services, production/public beta or physical-field claims.
