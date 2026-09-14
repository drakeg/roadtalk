# Sprint 10 D05 — Campground communication context evidence

## Scope

D05 implements S10-R06 / S10-T06 by adding a campground communication composition layer that consumes an already-authorized RoadTalk receiver set and can only narrow it.

## Requirement mapping

- **S10-R06 / S10-T06 authorization preservation:** `backend/app/campgrounds/communication.py` accepts `already_authorized_receivers` as its only receiver source. It never queries or constructs new eligible receivers, and matching campground context can only retain or remove entries from that upstream set.
- **Campground context is not authorization:** `CampgroundCommunicationContext.authorization_source` remains fixed to `existing_roadtalk_authorization`, and the composition layer does not modify channel membership, PTT grants, notification eligibility, proximity policy, Same-road filtering, or media grants.
- **Fail-closed lifecycle:** missing or expired sender context makes the campground communication surface unavailable. Missing, expired, or different receiver context removes that receiver from the campground-specific composition. D04 derivation supplies the active-account, consent, current-location, and source-session lifecycle checks.
- **No membership/occupancy exposure:** the public communication context contains only `campground_id`, `context_only`, and `authorization_source`. Tests reject membership, occupancy, and recipient-list fields.
- **No new persistence/history:** D05 adds no migration or database model and retains no campsite/unit presence, occupancy, arrival/departure, visit, or location history.
- **$0 boundary:** deterministic local/CI campground data and existing RoadTalk services only; no external provider, cloud activation, credentials, reservation/payment capability, or recurring spend.

## Test coverage

`backend/tests/test_campground_communication.py` verifies:

- the output receiver set is a strict subset of the upstream authorized set and cannot add an account that was not supplied upstream;
- missing or expired sender context fails closed;
- stale or different campground receiver context is removed;
- the public context exposes no membership, occupancy, or recipient-list data.

## Acceptance boundary

Merging D05 accepts only the Sprint 10 campground communication-context composition. It does not authorize an external campground data source, AWS/LiveKit Cloud activation, reservation/booking/payment features, campground occupancy tracking, background location/audio, production/public beta, or Sprint 11 work.
