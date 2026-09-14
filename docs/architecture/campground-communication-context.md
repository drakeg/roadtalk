# Campground communication context

Sprint 10 D05 adds a campground-specific communication composition layer without creating a new authorization source.

## Composition order

1. Existing RoadTalk account, session, location-consent, current-location, channel/private-channel, proximity, Same-road, media-grant, and notification rules determine who is already eligible.
2. D04 derives an ephemeral current campground label from that existing authorized current state.
3. D05 receives only the already-authorized receiver set and may narrow it to receivers whose current campground label matches the sender's current campground.
4. The public campground communication contract exposes only the campground ID plus fixed markers that the context is descriptive and authorization remains owned by existing RoadTalk rules.

The campground layer never discovers a new recipient, restores an upstream denial, grants PTT/media/notification eligibility, or changes channel membership.

## Fail-closed lifecycle

A campground communication composition is unavailable when the sender has no current campground context or that context has expired. Receiver entries are removed when their current campground context is missing, expired, or different. D04 derivation already requires active account state, current granted location consent, usable non-stale current location, and an active source-device session, so logout, revocation, consent withdrawal, account disablement, deletion of current state, and stale location naturally remove campground context.

## Privacy boundary

No campground member list, exact occupancy count, campsite/lot/unit identity, coordinates, distance, arrival/departure event, visit history, route/destination inference, or arbitrary recipient targeting is exposed by the campground communication contract. D05 adds no persistence table and retains no campground-presence history.

## Cost and provider boundary

D05 uses the deterministic local/CI campground catalog and existing RoadTalk authorization state only. It activates no campground/place/map/reservation provider, external network dependency, cloud service, credential, booking/payment capability, or recurring spend.
