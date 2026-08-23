# Route-context provider boundary

Status: Sprint 7 S07-D03 local/GitHub-CI implementation boundary.

RoadTalk's route-context boundary converts one already-accepted foreground location sample into a short-lived, minimized semantic match. It does not expose a client-callable route-matching API and does not authorize a real routing service or road dataset.

## Request contract

The backend may pass only the accepted sample's latitude, longitude, horizontal accuracy, optional heading, optional speed, observed timestamp, and source location version. Extra fields are rejected. Clients cannot provide a road, corridor, provider, destination, route, direction, confidence, policy, TTL, or audience selector.

## Result contract

A provider result is limited to an opaque provider-scoped corridor reference, coarse direction bucket, confidence class, source location version, provider version, policy version, match timestamp, and expiry timestamp. Extra payload is rejected. Raw provider responses, road names, snapped points, geometry, traces, addresses, destinations, and route history do not cross this boundary.

The matcher validates source-version equality, policy-version equality, bounded TTL, freshness, and timeout behavior. Failures collapse to the stable semantic error `route context unavailable`; provider payloads and corridor references are not included in errors.

## Sprint 7 provider policy

`ROADTALK_ROUTE_CONTEXT_PROVIDER` accepts only `disabled` or `fake` and defaults to `disabled`. The fake provider uses deterministic in-memory fixtures for local tests and GitHub CI. It performs no network request and consumes no external dataset.

Field-test and production settings reject the fake provider. No URL, API key, secret, access token, OSRM adapter, OpenStreetMap dataset, routing container, hosted routing service, AWS resource, or paid provider is configured by S07-D03.

Any real adapter or dataset requires a separate dated product decision covering provider selection, privacy, licensing/attribution, data preparation and updates, availability, latency, rate limits, operations, and recurring cost.

## Deferred lifecycle

S07-D03 defines and validates the boundary only. It does not persist current route context or use route context for authorization. Those behaviors remain locked to S07-D04 and later deliverables in tracker #173.
