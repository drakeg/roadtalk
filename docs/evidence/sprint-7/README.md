# Sprint 7 route-awareness evidence

- Sprint: 7 — Route Awareness
- Deliverable: S07-D08 hardening/evidence baseline
- Current and incremental cost: **$0/month**
- AWS/LiveKit Cloud/routing-provider resources created: **none**
- External routing/map calls or dataset downloads: **none**
- Live-provider, physical-device, and field status: **not performed**

## Automated evidence

The authoritative D08 pull-request CI runs the full backend/PostGIS/migration suite,
mobile quality suite, dependency/privacy/scope gates, disabled Terraform/TFLint checks,
Trivy scans, container build/scan, and the Sprint 7 route-awareness hardening gate.

The route-aware database scale test uses a migrated disposable PostGIS database with:

- 100 registered accounts;
- 25 connected receive grants;
- 10 active publishers;
- five Nearby publishers and five Same-road publishers;
- 20 receiver contexts on the matching corridor with compatible coarse direction;
- five route-denied receiver contexts using a different corridor or incompatible direction;
- one Same-road publisher whose corridor has zero compatible recipients.

The first authoritative D08 hardening run was GitHub Actions **Sprint 7 hardening #1**
(run `33035376277`) on 2026-08-27. Its measured control-plane p95 values were:

- Nearby eligible lookup p95: **40.71 ms**;
- Same-road eligible lookup p95: **24.03 ms**;
- Same-road zero-recipient denial p95: **18.97 ms**;
- bounded publication/subscription reconciliation p95: **160.94 ms**;
- control-plane target: **400 ms p95**.

All measured categories were below the 400 ms target. The test and CI workflow enforce
the ceiling on every future run; the values above are evidence from that named run,
not a permanent benchmark claim. Synthetic timing proves only the tested disposable
PostGIS/control-plane path; it does not prove WebRTC media, routing-provider latency,
device GPS quality, or production capacity.

## Privacy and security evidence

Automated/static gates require that:

- Nearby remains the default and Same-road can only reduce an already-authorized set;
- route-mode APIs accept only the approved exact mode/version contract;
- no client-callable matching endpoint exists;
- the provider boundary remains `disabled`/deterministic `fake` only and contains no
  network client, provider URL, credential, OSRM or OpenStreetMap implementation;
- current route context remains one minimized row containing a keyed 64-character
  corridor digest, coarse direction/confidence, source location version, provider/policy
  version and short timestamps only;
- no road name, snapped point, route geometry, trace, destination, itinerary, provider
  payload, exact distance/bearing, other-user identity, or eligibility explanation is
  exposed through the approved route experience;
- semantic logs/aggregate metrics continue to discard route/corridor/direction/location,
  identity, provider and eligibility detail;
- missing, expired, ambiguous, mismatched, stationary/unknown or failed route context
  denies Same-road rather than silently widening to Nearby;
- pause, withdrawal, logout, deletion, revocation and route-mode/location transitions
  retain the bounded fail-closed lifecycle established in D04–D06.

## Provider and dataset activation boundary

A real routing provider is **not selected or activated**. OSRM remains only a candidate
adapter. No public OSRM demo endpoint, OpenStreetMap API/tile endpoint, hosted route API,
regional road graph, routing container, credential, API key, account, payment method or
network request is part of Sprint 7 evidence.

Any future OpenStreetMap-derived dataset activation must have a dated architecture and
product decision that records at minimum:

- Open Database License (ODbL) attribution obligations;
- share-alike obligations applicable to any produced derivative database;
- dataset source/version/geographic scope and update process;
- distribution/attribution text and where users/operators will see it;
- provider terms, rate limits, privacy handling, retention and availability;
- storage/compute/network size, operating responsibility and recurring-cost estimate.

No free public OSM or OSRM service is assumed to be production infrastructure.

## Cost evidence

Current and incremental Sprint 7 recurring cost remains **$0 AWS + $0 LiveKit Cloud +
$0 routing provider per month**. Terraform remains disabled and is required to validate
without creating resources. The local Docker Compose stack and deterministic fake
provider are the only approved implementation/evidence environment.

No budget alert, CI gate, quota, or cost ceiling is an automatic shutdown control and
none authorizes provider/cloud activation or recurring spend.

## Explicit evidence exceptions

The following were **not performed** and must not be represented as passed:

- real-road matching quality, ambiguity rate, map completeness or freshness;
- real routing-provider availability, latency, quota or failure behavior;
- licensing compliance for a selected/distributed production road dataset;
- physical-device GPS accuracy, permission UX, battery/data use or background behavior;
- physical microphone/speaker, Bluetooth, interruption or accessibility-gesture behavior;
- live media latency/jitter/loss, cellular/Wi-Fi handoff, NAT/TURN or live subscription revocation;
- AWS deployment, billing, destroy, production/public beta or multi-worker capacity;
- safety, emergency, hands-free or navigation claims.

The browser secure-context/microphone/location behavior added in PR #183 is automated
and code-reviewed evidence only. Cross-browser/physical-system verification remains a
field exception until explicitly performed.
