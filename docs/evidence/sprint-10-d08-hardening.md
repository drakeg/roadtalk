# Sprint 10 D08 — campground reliability and privacy hardening

This deliverable hardens the campground feature against stale state, enumeration, privacy leakage, and authorization drift.

## Locked properties

- Campground context remains server-derived from existing authorized current-location state.
- Clients cannot select a campground to gain communication eligibility.
- Campground context can only narrow or label an already-authorized RoadTalk communication set.
- Missing, stale, revoked, logged-out, deleted, or consent-withdrawn current state fails closed.
- Public campground contracts expose no campsite/unit identity, exact occupancy, member list, arrival/departure record, or durable visit history.
- Malformed or over-posted campground data is rejected by closed Pydantic contracts.
- Errors and public responses do not reveal whether a specific person is or was at a campground.
- No external provider, network activation, analytics, background tracking, booking/payment capability, or recurring spend is introduced.

## Regression coverage

Existing Sprint 10 tests verify bounded deterministic catalog data, no client campground selector on current-context derivation, ephemeral context expiry, and campground communication narrowing. D08 adds explicit privacy/contract regression coverage for over-posting, prohibited fields, stale context, and the absence of client-supplied authorization inputs.

Current and incremental recurring cost: $0.
