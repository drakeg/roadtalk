# Same-road media authorization

Sprint 7 D05 composes Same-road as a restrictive server-side filter over the already
accepted Sprint 5/6 receive-grant candidate set.

## Authorization order

1. The existing PostGIS proximity query first applies account, device, session,
   location consent/freshness/accuracy, channel selection/membership, receive-grant,
   room, policy and `ST_DWithin` predicates.
2. Only those already-authorized candidates are inspected for route mode.
3. Nearby/Nearby pairs remain eligible without route context.
4. If either endpoint selected `same_road`, both endpoints require current confident
   route context bound to the current accepted location version.
5. The keyed corridor digests must match exactly and coarse directions must be
   compatible.
6. Missing, expired, source-mismatched, unknown, stationary, corridor-mismatched or
   direction-incompatible context removes the receiver from the candidate set.

The route filter only iterates the candidate tuple returned by the prior authorization
query. It has no code path that can introduce a new receiver, so a prior denial cannot
become eligible through Same-road.

## Direction policy

Travel directions use the eight coarse compass buckets in circular order. The same
bucket or one adjacent bucket is compatible. This makes north/northwest and
north/northeast wraparound deterministic while rejecting wider/opposite direction
separation. `stationary` and `unknown` are never considered Same-road compatible.

No heading, road name, provider corridor reference, coordinate, distance, bearing or
eligibility reason is returned to a client.

## Media behavior

Transmit creation and publication use the composed candidate finder. Selective media
subscription remains server-authorized; automatic subscription remains disabled.
Existing reconciliation recomputes the same composed eligibility set, unsubscribes the
bounded ineligible set first, then subscribes the remaining eligible set. Empty or
failed authorization therefore fails closed rather than falling back to Nearby.

No routing provider, map service, dataset, cloud resource, background process or paid
service is added by this deliverable.
