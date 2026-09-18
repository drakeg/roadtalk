# Registered account login

RoadTalk supports persistent registered accounts without requiring email, phone, OAuth, Cognito, or another hosted identity provider.

## Identity model

- A private username and password authenticate the RoadTalk account.
- The public call sign remains part of the account profile and is not used as the login credential.
- New registration atomically creates the account, credential, public call sign, and
  active web-default avatar so a partial registered identity is never exposed.
- A call sign therefore follows the account across browser sessions and devices.
- Logging out revokes only the current session; it does not delete the account, profile, or call sign.

## Existing guest identities

An authenticated anonymous account can be promoted in place through `POST /api/v1/auth/promote`. Promotion changes `account_type` to `registered` and adds a registered credential while preserving the existing account id and all account-owned state, including the profile/call sign, channel state, and other persisted settings.

If the anonymous account is no longer authenticated, use the existing recovery-key flow to recover that account before promotion. RoadTalk does not reassign a call sign from an existing account based only on knowledge of the call sign.

## Browser flow

The browser home route (`/`) is a privacy-limited dashboard. It reports service
readiness, session type, and the account's public call sign when available, without
displaying account, device, session, route, or location identifiers. Web Radio lives
at `/radio`; browsers without a saved access or refresh credential are directed to
`/account` before Web Radio creates a guest identity. The account page presents
separate **Log in** and
**Create account** forms. Creation requires a private username, password confirmation,
and public call sign; the server assigns the active web-default avatar in the same
transaction. A browser with an authenticated guest profile and call sign can instead
use **Protect this existing profile** to promote that same account without changing
its account id, call sign, avatar, or account-owned state.

If another account—including an anonymous account—already owns the requested call
sign, registration fails without creating a partial account. RoadTalk does not infer
ownership from knowledge of a call sign and does not silently release or reassign it.

## Password handling

Passwords are never stored directly. RoadTalk stores only a versioned, randomly salted scrypt hash. Login uses the same failure shape for an unknown username and an incorrect password. Authentication credentials are not part of public identity, map presence, or PTT payloads.

## Cost and deployment

This feature uses the existing API process and PostgreSQL database only. It adds no AWS resource, hosted identity provider, payment method, or recurring service cost.
