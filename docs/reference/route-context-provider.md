# Route-context provider boundary

Sprint 7 S07-D03 introduces an internal route-context matching boundary without activating a real routing provider.

## Allowed implementations

- `disabled` is the default in every environment.
- `fake` is permitted only in `local` and `test` environments for deterministic fixtures.
- `field-test` and `production` reject any non-disabled route-context provider.
- No OSRM, OpenStreetMap, hosted routing API, road dataset, routing container, credential, or network client is included.

## Minimized request

The provider receives only the already-approved current foreground location sample fields needed for matching: latitude, longitude, horizontal accuracy, optional heading, optional speed, observation time, and source location version. Extra fields are rejected.

The client cannot call this provider boundary directly and cannot submit a road, corridor, provider, destination, address, route, direction bucket, confidence, audience selector, or provider hint.

## Validated result

The in-memory provider result contains only an opaque provider-scoped corridor reference, coarse direction, semantic confidence, source location version, provider version, policy version, match time, and short expiry. Extra/raw provider payloads are rejected.

`RouteContextMatcher` enforces a bounded timeout, matching source location version, expected policy version, maximum TTL, and freshness. Provider timeouts, malformed results, mismatches, and unexpected exceptions become the stable non-disclosing `route context unavailable` failure.

The provider-scoped corridor reference introduced here is transient. S07-D04 is responsible for keyed/non-portable persistence and lifecycle; this deliverable does not add route-context persistence.

## Deterministic fake

The fake provider uses an injected mapping of rounded synthetic coordinate fixtures to a compact corridor/direction/confidence result. It performs no file, dataset, DNS, HTTP, socket, cloud, or provider access.

## Cost and activation

Current and incremental implementation cost remains **$0 AWS + $0 LiveKit + $0 routing provider per month**. Real provider selection, adapter implementation, data licensing/attribution, dataset preparation, deployment, and activation require a separate dated decision outside S07-D03.
