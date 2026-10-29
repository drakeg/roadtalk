# Sprint 14 D06 evidence — browser Premium experience

## Deterministic evidence

- `GET /api/v1/me/premium` requires authentication, is read-only, ignores any account selector and reads only the caller's account (`tests/test_premium_web.py`).
- The default disabled provider reports `provider_disabled` / `free` without contacting a provider.
- Every subscription state maps through the central D05 gate; only `active`, `grace` and `canceled` grant the Premium experience (`tests/test_premium_status.py`).
- Provider failure and cross-account provider results fail closed with a generic status and no provider error text.
- Status is server-stamped with a 5-minute `valid_until` and sent `no-store`.
- The `PremiumStatus` contract is closed (`additionalProperties: false`) and carries no payment, provider credential, location or unrelated-user field.
- The `fake` provider is rejected by settings validation for `field-test` and `production`.
- The `/premium` page is accessible (live status region, labelled sections, `type="button"` explicit action, `:focus-visible`), states baseline preservation, offers no checkout or payment fields, clears status on expiry/offline/failure, does not poll, and does not persist Premium state client-side.

Validation: `pytest` full backend suite passes; a local headless-Chromium (Playwright) run against the fake provider rendered the active status with provenance, cleared it on going offline, and re-read it on the explicit button with no page errors; `ruff format --check`, `ruff check` clean; `mypy` reports no new errors.

## Requirements covered

- S14-R02 / S14-T02 — Premium status cannot create communication eligibility; the page states this.
- S14-R05 / S14-T05 — status uses the central D05 gate.
- S14-R06 / S14-T06 — browser accessibility, explicit action, provider-disabled, offline and stale clearing.
- S14-R09 / S14-T09 — closed, privacy-bounded status contract.
- S14-R11 / S14-T11 — provider stays disabled by default and cannot be enabled outside local/test; $0 incremental cost.

## Evidence exceptions — NOT PERFORMED

No live payment/store provider, checkout, real-money transaction, physical-device or real-browser accessibility audit, screen-reader session, production/public-beta operation, tax/refund/chargeback flow or provider billing evidence is claimed. CI verifies browser behavior through served-markup assertions; the headless-Chromium run above was a local check, not a CI gate.
