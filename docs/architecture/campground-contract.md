# Campground contract

Sprint 10 D02 locks the campground domain and privacy contract before persistence, current-context composition, communication behavior, browser/mobile UX or external data-source decisions.

## Public campground record

The public contract contains only a stable opaque campground ID, name, category, coarse public campground location, bounded amenity flags and explicit deterministic source/freshness context. Campground coordinates represent the campground itself at `campground_centroid` precision; they are not user coordinates or a user-presence record.

Allowed Sprint 10 categories are `public`, `private`, `state_park`, `national_park`, `county_municipal` and `other`.

Local/GitHub-CI D02 data source and freshness are fixed to `deterministic_local` / `deterministic`. This prevents deterministic test fixtures from being represented as a live or complete campground directory.

## Privacy exclusions

The contract deliberately contains no account/user/device/recipient identity, private contact or authentication field, campsite/lot/unit identifier, exact occupancy/member list/count, person-presence list, arrival/departure timestamp, visit/location history, route/corridor/destination, user motion, arbitrary radius/distance/bearing, provider credential or audience override.

No later Sprint 10 layer may reinterpret campground data as permission to reveal a person, campsite, occupancy or visit history.

## Search contract

Campground search is bounded to text, category, region, one approved amenity and a 1–100 result limit. D02 does not accept caller-selected coordinates, radii, provider controls, recipient controls or occupancy/history filters.

D03 may implement deterministic catalog search using this contract. A real campground/place/map/reservation provider remains outside the approved boundary until separately reviewed for licensing, attribution, caching/storage, privacy, freshness, quota and cost.

## Communication context

Campground communication context is explicitly labeled `context_only = true` with `authorization_source = existing_roadtalk_authorization`.

This is an invariant, not descriptive copy: campground context cannot create PTT, listener, channel, notification or recipient eligibility. Existing account/session/location-consent/current-location/proximity/channel/Same-road/media/notification authorization remains authoritative. Campground logic may only narrow or label already-authorized state.

## Explicit exclusions

D02 does not add persistence, campground boundary detection, current user presence, visit history, occupancy calculation, channel creation, PTT changes, browser/mobile UX, background location/audio, reservation inventory, booking/payment behavior, scraping, external provider/network calls, analytics or cloud resources.

Current and incremental recurring cost remains $0.