# Sprint 10 D09 — campground scale, provider, and compatibility evidence

Issue: #253  
Requirements: S10-R11 / S10-T11

## Enforced boundary

D09 adds a dedicated regression gate over the campground privacy/provider boundary and locks the synthetic performance targets before the named evidence run.

The existing closed campground contracts remain authoritative: no exact person-to-campground or campsite history, campsite/unit identifiers, occupancy/member enumeration, arrival/departure history, or client-selected communication authorization is part of the public/runtime contract.

The runtime must not acquire external campground/place/map/reservation provider credentials. Sprint 10 remains deterministic and local/CI-only; provider activation, scraping, analytics, background tracking, booking/payment capability, and spend-enabling dependencies remain outside scope.

## Named matrix and measurements

The named D09 run is defined in `sprint-10-d09-targets.md` and must use at least 100 accounts, 25 valid current-context users, 10 campground communication publishers, and a representative deterministic campground catalog.

Search, current-context derivation, and campground authorization composition are measured separately against their pre-locked p95 targets. A campground composition result is valid only when it is a subset of the already-authorized RoadTalk recipient set.

## Compatibility statement

Passing local/CI evidence demonstrates deterministic catalog behavior and regression compatibility with the existing RoadTalk authorization/privacy model. It does not demonstrate real provider freshness or licensing, physical-device compatibility, WAN/mobile-network behavior, production scale, or public availability.

## Cost

Current recurring cost: $0.  
Incremental recurring cost introduced by D09: $0.
