# Sprint 10 D06 — browser campground experience

## Purpose

The `/campgrounds` surface provides accessible browse/search/filter behavior for the deterministic Sprint 10 campground catalog and explains the current-context boundary without turning campground selection into authorization.

## Data and privacy boundary

- `/api/v1/campgrounds/catalog` exposes only the bounded `CampgroundPublicRecord` contract and explicitly reports `source=deterministic_local`, `freshness=deterministic`, and `live_directory=false`.
- `/api/v1/campgrounds/context` requires the existing authenticated RoadTalk session and derives context server-side from the D04 authorized-current-state path. It accepts no campground selector.
- Campground browsing does not add recipients, restore an upstream denial, create membership, or imply campground occupancy.
- The browser receives no campsite/unit identity, member list, occupancy count, arrival/departure history, durable visit history, or provider credentials.
- No external campground, map, reservation, booking, payment, or availability provider is contacted.

## Browser behavior

The page uses native search/select controls, keyboard-visible focus, live status regions, responsive card layout, and text labels rather than color-only state. Search and filters operate only on the already-bounded deterministic catalog response.

Current campground context is described as server-derived and authorization-neutral. Missing, stale, degraded, revoked, or unavailable location state must remain unavailable rather than presenting prior context as current.

## Cost and deployment

D06 adds no paid service, external provider account, recurring spend, production activation, background location, or background audio. Current and incremental recurring cost remains $0 under the Sprint 10 authorization boundary.
