# Convoy communication authorization

Sprint 11 D04 composes convoy context as a restrictive server-side filter over the already-authorized RoadTalk receive candidate set.

## Authorization order

1. Existing account, device, session, location-consent/freshness/accuracy, selected-channel/membership, receive-media-grant, room/policy and PostGIS proximity rules produce the candidate set.
2. Same-road filtering may narrow that set under its existing policy.
3. Convoy composition receives only that already-authorized tuple and has no path that can add a recipient.
4. If the sender has no active, unexpired membership in an active convoy, D04 does not alter the prior authorization result.
5. If the sender has active convoy context, only candidates with active, unexpired membership in that same convoy remain eligible.
6. Left, revoked, expired, unknown membership and disbanded convoy state therefore remove convoy-scoped recipients immediately.

Convoy membership never creates account/session validity, location consent, current-location validity, proximity or Same-road eligibility, channel membership, recipient eligibility, or media grants. It cannot select a provider room, override a recipient, or bypass a prior denial.

## Privacy and operational boundary

The filter queries only durable convoy/member identifiers and lifecycle state already introduced by D03. It does not persist or return coordinates, routes, presence snapshots, unrelated-user membership, background location/audio, provider credentials, or eligibility reasons.

D04 adds no provider/network integration, cloud resource, worker, analytics system, or recurring spend. Incremental recurring cost remains $0.
