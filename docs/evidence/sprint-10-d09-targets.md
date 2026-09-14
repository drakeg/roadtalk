# Sprint 10 D09 — locked evidence targets

These targets are locked before the named Sprint 10 campground evidence run.

## Synthetic matrix

The named run must use at least:

- 100 accounts
- 25 accounts with valid current campground context
- 10 campground communication publishers
- a representative deterministic campground catalog

## Performance targets

Measure each path separately; do not combine them into one latency figure.

- deterministic campground search p95: <= 500 ms
- current campground context derivation p95: <= 750 ms
- campground communication authorization composition p95: <= 1500 ms

## Required assertions

The run must preserve the existing RoadTalk authorization set before campground narrowing. Campground context may retain or remove already-authorized recipients only; it may never add a recipient or restore an upstream denial.

Evidence must also demonstrate that the campground surface does not expose exact person-to-campground history, campsite/unit identity, exact occupancy/member enumeration, arrival/departure history, or client-selected communication authorization.

## Evidence boundary

This is deterministic local/GitHub-CI evidence only. It is not evidence for real provider freshness, provider licensing, physical-device behavior, WAN/mobile-network behavior, production capacity, or public availability.

No external campground/place/map/reservation provider, scraping, analytics, background tracking, cloud activation, paid plan, credential, booking/payment capability, or recurring spend is authorized. Current and incremental recurring cost remains $0.
