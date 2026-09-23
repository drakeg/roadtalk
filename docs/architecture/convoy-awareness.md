# Current convoy awareness

Sprint 11 D05 derives a bounded, member-visible convoy awareness snapshot from RoadTalk's authoritative current state. The snapshot is computed on demand and is not persisted.

A viewer must have active, unexpired membership in an active convoy. Non-members receive no convoy awareness and the query does not enumerate another convoy. Visible entries are restricted to active, unexpired members of that same convoy whose account is active and whose existing foreground current-location state remains usable, unexpired, covered by current granted consent for the active location policy, and backed by an active source session.

The member-visible payload contains only the account identifier, callsign, convoy role, the fixed state `current`, and an expiry timestamp. It contains no coordinates, approximate coordinates, heading, speed, route/corridor, location age/history, provider data, unrelated nearby users, or authorization reasons.

The snapshot expires at the earliest included authoritative current-location expiry. If no member currently qualifies, the authorized snapshot is empty and expires immediately. Location deletion, consent loss/change, source-session revocation, account disablement, membership leave/revoke/expire, convoy disbandment, or current-location staleness therefore fails closed on the next derivation.

D05 adds no background collection, durable awareness/location history, worker, external provider, cloud resource, analytics system, or recurring spend. Incremental recurring cost remains $0.
