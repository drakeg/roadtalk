# Sprint 14 D07 evidence — mobile Premium experience

## Deterministic evidence

- `PremiumApi.test.ts` (17 tests): bodiless caller-only `GET /me/premium`; generic failure for HTTP, network and parse errors; the closed parser rejects unknown/missing fields, checkout claims, non-authoritative payloads, tier/gate disagreement, Premium without an active entitlement or available provider, unknown states, bad timestamps and validity windows outside (0, 5 min].
- `PremiumScreen.test.tsx` (6 tests): server-confirmed status with provenance; baseline-preservation and no-purchase statements; no buy/subscribe/upgrade control; provider-disabled shows no Premium; status is cleared on failed re-check, at `valid_until`, and when the app leaves the foreground; an in-flight result arriving after the app was backgrounded is discarded; no request without an authenticated session.
- A mutation check confirmed the foreground test fails if the in-flight discard is removed.

Validation: `npm run typecheck` clean; `npm test` 40 suites / 227 tests pass.

## Requirements covered

- S14-R02 / S14-T02 — the screen states Premium never changes communication eligibility; status comes only from the server.
- S14-R06 / S14-T06 — mobile accessibility, explicit action, provider-disabled, offline/failure, foreground-only and stale clearing.
- S14-R09 / S14-T09 — no payment, store or location data in the request or the accepted response.
- S14-R11 / S14-T11 — no store/payment dependency added; $0 incremental cost.

## Evidence exceptions — NOT PERFORMED

No physical-device run, App Store / Google Play sandbox or production purchase, screen-reader session on a device, live provider, production/public-beta operation, tax/refund/chargeback flow or provider billing evidence is claimed.
