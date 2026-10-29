# Premium mobile experience

Sprint 14 D07 (#351) adds the mobile counterpart of the D06 browser view. It reads the same server contract (`GET /api/v1/me/premium`, see [premium-browser-experience.md](premium-browser-experience.md)) and adds no purchase, store or payment path.

## Client contract handling

`mobile/src/premium/api.ts` accepts only the closed `PremiumStatus` shape. It rejects the payload, and shows no status, when:

- any field is missing or unexpected;
- `checkout_available` is not `false`, or `server_authoritative` / `communication_authorization_unchanged` is not `true`;
- `tier` disagrees with `premium_experience_allowed`;
- Premium is claimed without `availability: available` and an `active` entitlement;
- timestamps are invalid, or the `observed_at` → `valid_until` window is empty or longer than 5 minutes.

The request is a bodiless authenticated `GET` with no account or tier parameters. Network, HTTP and parse failures collapse to one generic error.

## Screen behavior

`PremiumScreen` (Home → **Premium**):

- reads status when opened with an authenticated session and re-reads only on the explicit **Check Premium status** button; there is no polling or background refresh;
- clears displayed status when it reaches `valid_until`, when the app leaves the foreground (`AppState` not `active`), when a check fails, and when there is no authenticated session;
- discards any in-flight response that completes after a clear, so stale data can't reappear;
- announces status through an `accessibilityLiveRegion`, uses header roles and a labelled button with busy/disabled state;
- shows provenance (server time and whether the deterministic test provider answered) and validity;
- never persists Premium state on the device;
- states that Premium never changes who you can hear or talk to, and that purchase is not available.

## Scope

D07 does not add store/payment SDKs, product IDs, prices, receipts or background tasks. Replay/webhook hardening is D08.
