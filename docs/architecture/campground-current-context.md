# Campground current-context composition

Sprint 10 D04 derives campground context from RoadTalk's existing authorized current-location state. The campground layer is descriptive context only; it is not a new authorization or tracking source.

## Derivation boundary

`derive_current_campground_context` accepts only the authenticated account identity supplied by the server, the active location-policy version, and server time. It does not accept a client-selected campground, campsite, audience, recipient list, occupancy value, route, destination, distance, or authorization override.

A current point is eligible only when the existing RoadTalk state is already usable: the account is active, the current location is unexpired and usable, the current location carries the active consent policy, the latest consent decision is granted for that policy, and the source device still has an unrevoked, unexpired session. Failure of any prerequisite returns no campground context.

After that existing authorization gate passes, the point is compared with deterministic local/CI campground centroids. The internal deterministic distance policy is test scaffolding, not a claimed campground boundary, provider result, occupancy radius, or public API field. The nearest qualifying deterministic record becomes a short-lived label whose expiry is inherited from the authorized current location.

## Privacy properties

The derived result contains only campground ID, public campground name, `current` state, and inherited expiry. It contains no account/device identity, exact user coordinates, distance, campsite/unit, member list, occupancy count, arrival/departure time, visit history, route/destination, audience, recipient set, or provider credential.

No campground-presence table or history is created. Context is recomputed from current state and disappears when that state expires or becomes ineligible. Logout/session revocation, account disablement/deletion, stale location, degraded location, or consent withdrawal therefore fail closed through the existing authoritative state.

## Authorization invariant

Campground context can label or narrow a result only after existing RoadTalk authorization succeeds. D04 provides no mechanism that can restore a recipient, publisher, listener, channel membership, proximity result, Same-road result, media grant, or notification denied by an upstream Sprint 3–9 rule.

This implementation remains local/GitHub-CI only, uses deterministic campground data, adds no external provider/network dependency, and adds no recurring spend.
