# Premium browser experience

Sprint 14 D06 (#350) adds a read-only browser view of the caller's server-confirmed Premium status. It introduces no checkout, purchase, payment collection or store/provider activation.

## Server status contract

`GET /api/v1/me/premium` requires an authenticated RoadTalk session and returns the closed `PremiumStatus` contract for the caller's own account only. It accepts no account selector and has no write methods. Responses are `Cache-Control: no-store`.

| Field | Meaning |
|---|---|
| `availability` | `available`, `provider_disabled` or `provider_unavailable` |
| `provider_mode` | `disabled` or `test` (deterministic fake; no billing) |
| `tier` | `premium` only when the central D05 gate allows the Premium experience; otherwise `free` |
| `entitlement_state` | Entitlement derived from the provider's subscription state, or `null` when none was observed |
| `premium_experience_allowed`, `reason` | The D05 gate decision |
| `observed_at`, `valid_until` | Server observation time and the end of its 5-minute trust window |
| `checkout_available` | Always `false` |

The status is computed by `app.premium.status.read_premium_status`, which calls the D03 provider boundary and passes the result through the D05 gate. Subscription state maps to entitlement as: `active`, `grace`, `canceled` → `active` (cancellation keeps entitlement through the already-authorized period); `inactive`, `expired`, `revoked` → the same entitlement state. A provider observation is trusted only for `ENTITLEMENT_MAX_OBSERVATION_AGE`, so `valid_until` is never more than 5 minutes after `observed_at`.

Provider failures, timeouts and cross-account results collapse to a generic `provider_unavailable` status with no entitlement; provider error text is never returned.

## Provider configuration

`ROADTALK_PREMIUM_PROVIDER` defaults to `disabled`. `fake` is accepted only in `local` and `test` environments; settings validation rejects it for `field-test` and `production`. With the default, the page reports that Premium is not available in this environment.

## Browser page

`/premium` (linked from the dashboard):

- loads status once on open and re-reads only on the explicit **Check Premium status** button; there is no polling;
- announces state through a `role="status"` live region and uses visible focus indicators;
- shows provenance (RoadTalk server time, and that the test provider has no billing) and when the status stops being valid;
- clears displayed status when it reaches `valid_until`, when the browser goes offline, and when a check fails;
- renders with `textContent` only and never stores Premium state in browser storage;
- states that Premium never changes who you can hear or talk to and that all existing features remain available without Premium;
- states that purchase is not available and contains no form or payment fields.

## Scope

D06 does not add the mobile experience (D07), webhook/replay hardening (D08), or any live payment/store provider, price, product ID, tax or refund behavior.
