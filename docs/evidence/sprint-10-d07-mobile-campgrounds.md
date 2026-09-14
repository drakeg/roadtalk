# Sprint 10 D07 — Mobile campground experience

Issue: #251  
Requirements: S10-R08  
Tests: S10-T08

## Delivered

- Added an authenticated mobile Campgrounds screen backed by the bounded Sprint 10 campground APIs.
- Mobile discovery uses only deterministic local/CI campground records and labels that provenance explicitly.
- Current campground context is read only from the D04 server-derived `/api/v1/campgrounds/context` contract; the mobile client cannot submit a campground selector or assert presence.
- Search operates only on returned public campground name/locality metadata.
- Communication entry routes to existing channel controls; campground state does not create or broaden channel, proximity, PTT, media, notification, or recipient authorization.
- Catalog/context failures, unavailable current context, permission-denied/no-location/stale state, and offline failures degrade to explicit unavailable states without inferred presence or stored visit history.
- No new background location permission, background audio permission, campsite/unit presence, occupancy/member list, visit history, reservation, payment, provider activation, or recurring spend was added.
- Accessibility includes explicit labels, live-region status text, minimum-height controls, and text descriptions that do not depend on color.

## Verification

- `mobile/src/__tests__/CampgroundApi.test.ts` locks bounded filtering and prohibited-data expectations.
- Existing mobile type-check/test workflow remains the acceptance gate for navigation, accessibility regressions, and prior Sprint behavior.
- Current and incremental recurring cost remains `$0`.
