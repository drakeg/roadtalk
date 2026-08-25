# Current route-context lifecycle

Sprint 7 S07-D04 persists only one short-lived current route context per account. It is internal server state and is never a client-callable route-matching surface.

## Persisted state

`current_route_context` contains only the account ID, a 64-character keyed corridor digest, coarse direction, confident-only state, the exact accepted current-location version, provider and policy versions, match/expiry timestamps, and a row version.

It stores no provider corridor reference, road name, snapped coordinate, road geometry, route, trace, destination, address, itinerary, raw provider payload, or history.

The corridor digest is a domain-separated HMAC-SHA256 value derived with an existing RoadTalk server secret. The provider corridor reference is used only transiently while deriving the digest and is not written to the database.

## Binding and replacement

A route context can be created only from the currently accepted, usable foreground location. The lifecycle holds a row lock on current location, requires Same-road mode, enforces usable accuracy/freshness, invokes the bounded provider matcher, accepts only confident results, requires the result to reference the exact current-location version, and refuses a route-context expiry beyond the source location expiry.

When RoadTalk accepts a newer current location, the prior route context is deleted in the same database transaction as the location replacement. The bounded route-context refresh runs afterward. This prevents an old context from remaining usable while a new provider match is pending or fails.

A replay of the exact same result for the same source-location version is idempotent. A conflicting result for the same source version fails closed by deleting the current context rather than replacing it.

## Cleanup

The route-context primary key also references `current_location.account_id` with `ON DELETE CASCADE`. Location pause, foreground-consent withdrawal, location expiry cleanup, and account deletion therefore remove current route context automatically. Switching to Nearby also deletes current route context. Ambiguous, stale, degraded, mismatched, expired, or provider-unavailable results leave Same-road context unavailable.

## Scope and cost

S07-D04 adds no map, navigation, route history, provider endpoint, dataset, external request, cloud resource, or paid service. The real routing-provider boundary remains disabled. Current and incremental recurring implementation cost remains $0 AWS + $0 LiveKit + $0 routing provider per month.
