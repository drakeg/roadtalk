# Sprint 3 synthetic foreground-location evidence

- Evidence type: automated tests plus repository inspection
- Synthetic-data rule: no real coordinate, callsign, account/device/session ID, or
  current physical location
- Baseline: merge commit `f2e1823d4510321a21432544550738121d6ab668`
- CI: [run 29546756307](https://github.com/drakeg/roadtalk/actions/runs/29546756307)
- Field-test status: not performed

## S03-T12 lifecycle demonstration

The lifecycle is demonstrated by deterministic tests using generated accounts,
devices, consent events, coordinates, times, movement values, and database rows.
Evidence records only test names and stable outcomes; generated location values and
identifiers are not retained in review artifacts.

| Lifecycle step | Automated evidence | Demonstrated outcome |
|---|---|---|
| Explain and choose | mobile `LocationPermissionScreen` and lifecycle tests | Purpose appears before the OS request; denial and continue-without-location remain usable. |
| Grant consent | consent unit/database and authenticated route tests | Current policy/disclosure grant is owner/device-scoped, versioned, idempotent, and coordinate-free. |
| Start foreground sampling | `never requests permission before...`; approximate-permission lifecycle test | Only foreground permission is requested after explicit enable; a native subscription starts only while active. |
| Validate sample | location quality boundary/time/sequence/movement tests | Malformed, stale, future, inaccurate, out-of-order, wrong-source, and implausible samples fail with stable non-disclosing codes. |
| Replace current row | `test_location_quality_replacement_consent_and_expiry_lifecycle`; persistence tests | A newer accepted sample replaces the sole current PostGIS row and returns metadata only. |
| Show owner-local quality | mobile quality/polling and permission-screen tests | Accuracy, optional heading/speed, and current/stale state are informational, owner-local, and unavailable safely. |
| Read coarse nearby | private indexed PostGIS eligibility and mobile semantic-contract tests | Only availability, none/few/many, freshness, and caller expiry are returned; no candidate field or exact value escapes. |
| Bound reads/writes | location limiter and route tests | Peer, account, and device dimensions return stable 429 responses and bounded `Retry-After`. |
| Expire and fail closed | expiry lifecycle, nearby missing/stale fixtures, and mobile expired-result test | Expired data becomes ineligible immediately; stale UI is not represented as current. |
| Pause and withdraw | idempotent deletion, consent revocation, and mobile pause tests | Pause removes the current row; withdrawal appends consent revocation and deletes location atomically. |
| Stop on lifecycle exit | background/screen/logout/dispose/native-failure/poll-cancellation tests | Native subscription, uploads, polling, timers, and process-memory location state stop and clear. |
| Delete source/account | migrated database cascade tests | Source-device or account deletion removes the current row without creating history. |

## S03-T10 privacy and scope evidence

- Exact OpenAPI path/schema allowlists reject coordinate output, account/device
  selectors, over-posting, and later-sprint routes.
- Closed structured logs reject synthetic latitude, longitude, accuracy, heading,
  speed, source-device, callsign, recovery, and non-allowlisted event fields.
- `scripts/ci/check-location-privacy.py` rejects background permissions/tasks,
  coordinate storage/logging, maps/geocoding, analytics, external providers, location
  history tables, and unapproved AWS/cache/scheduler dependencies.
- Mobile source/configuration tests prohibit TaskManager, geofencing, background
  flags, AsyncStorage/SecureStore location persistence, console logging, maps, and
  analytics.
- Nearby database tests cover empty, self, boundary, stale, inaccurate, degraded,
  withdrawn, and indexed-query-plan cases without retaining private fixture values.
- Terraform remains disabled and plans zero resources by default.

## Privacy-safe reproduction

Use the normal repository test targets and CI workflow. Do not paste generated
coordinates, motion values, callsigns, credentials, identifiers, request bodies,
concrete paths, screenshots containing values, or unrestricted logs into issues or
evidence. Record only commit, workflow run, test/gate name, pass/fail result, route
template, and stable problem code where necessary.

Follow [Foreground location operations](../../runbooks/location-operations.md) for the
approved synthetic rehearsal and incident boundary.

## What this does not prove

This record does not claim physical-device permission behavior, GPS accuracy, battery
performance, native storage inspection, clean-machine setup, enabled AWS resources,
deployed field testing, or production/multi-worker shared rate limiting. Those remain
outside Sprint 3 repository/CI evidence and are blocked by S01-E01 through S01-E03
where applicable.
