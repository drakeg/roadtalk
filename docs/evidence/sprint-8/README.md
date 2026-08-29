# Sprint 8 map/presence hardening evidence

This evidence record supports S08-D09 / S08-R11 / S08-T11. It is limited to local development and GitHub CI. Current and incremental recurring cost: **$0/month**.

## Locked synthetic scale target

The performance target was locked before the named evidence run: **400 ms p95** for both current-presence lookup/aggregation and repeated presence refresh.

The migrated disposable PostGIS matrix contains:

- **100 registered accounts**
- **25 presence viewers**
- **10 active publishers** with current foreground-approved usable locations
- five repeated refresh rounds across all viewers

`backend/tests/test_presence_scale.py` prints the named-run metrics as `Presence synthetic scale: {...}` and fails when either measured p95 exceeds the locked target. The measured values from the authoritative GitHub run will be recorded here before D09 is accepted.

- lookup/aggregation p95: **PENDING NAMED CI RUN**
- repeated refresh p95: **PENDING NAMED CI RUN**

## Privacy and lifecycle boundary

Presence remains current-only and derived from the existing current-location lifecycle. Another user's raw coordinate, exact count, account/device identity, call sign, distance, bearing, heading, speed, route/corridor/direction, destination, or history is not part of the nearby-presence API contract. Sparse cells remain suppressed below three distinct accounts, conflicting samples for one account fail closed, visible cells are bounded to 32, and the browser/mobile clients receive only approximate 2 km cell centers plus `few` / `several` / `many` density buckets.

Foreground location consent, usable location quality, active account status, a non-revoked non-expired source-device session, location-policy version, and location freshness remain required. The viewer is excluded from the other-user presence result. No presence history table is introduced.

## Provider, network, license, and cost boundary

The repository contains only the disabled provider and the deterministic local fake SVG tile provider. The hardening gate rejects external HTTP/network client markers, map service credentials, spend-enabling map/cloud dependencies, and provider expansion in the approved provider module.

**No production map provider selected.** Therefore this Sprint does not claim that a production map dataset/provider license has been satisfied. Before any production provider or dataset activation, a separate dated decision must record the selected provider/dataset, applicable **license and attribution** requirements, privacy/data-transfer impact, credential handling, pricing/free-tier constraints, expected recurring spend, rollback/disable path, and user-visible attribution obligations. No free public map/tile/geocoding/routing service is assumed to be production infrastructure.

## CI enforcement

`.github/workflows/sprint-8-hardening.yml` runs the migrated PostGIS scale test and `scripts/ci/check-map-presence-hardening.py`. Normal CI and the existing Sprint 7 hardening workflow remain authoritative for backend/mobile tests, migrations/schema drift, dependencies, secret scanning, container build/scan, Terraform zero-resource validation, and Sprint 5-7 privacy/authorization/performance regressions.

## Evidence limitations

Synthetic CI does not prove cellular-network behavior, GPS quality on moving physical devices, browser permission UX across every OS/browser combination, production map rendering quality, provider licensing compliance, or field safety. Physical compatibility evidence and explicit unperformed exceptions are recorded separately under S08-D08. No background location/audio or safety claim is introduced here.
