# Sprint 12 D08 — Moderation reliability, abuse and privacy hardening

Issue: #302

## Scope

This deliverable hardens moderation state creation against concurrent duplicate requests without broadening authorization or adding sensitive data collection.

## Reliability hardening

- Report creation now handles a database unique-index race by rolling back and re-reading the reporter-scoped idempotency row.
- An identical concurrent report is returned as the idempotent replay.
- A conflicting reuse of the same idempotency key fails with the existing generic `report unavailable` lifecycle error.
- Restriction creation now handles the active actor/subject/kind unique-index race by rolling back and re-reading the active restriction.
- An identical concurrent mute/block returns the existing active restriction.
- A collision without a matching active restriction fails with the existing generic `moderation unavailable` lifecycle error.
- Existing revoke and terminal-report transitions continue to use row locks and versioned terminal state.

## Privacy and abuse boundary

The hardening does not add request fields, durable evidence, raw location, route history, audio, credentials, provider secrets, unrelated-user presence, or authorization overrides. Database integrity errors are not surfaced to clients and do not create an account-enumeration distinction.

## Evidence

Deterministic backend tests cover:

- identical concurrent report replay after a unique constraint collision;
- mismatched concurrent report failure with a generic lifecycle error;
- identical concurrent active restriction replay after a unique constraint collision;
- restriction collision without a matching active row failing generically;
- rollback on every simulated integrity collision.

The existing Sprint 12 contract, authorization, persistence, limiter, browser, mobile and privacy tests remain authoritative for the rest of the D08 boundary.

## Exceptions

No physical-device, production, external provider, AWS, LiveKit Cloud, or public-beta evidence is claimed by this deliverable. Incremental recurring implementation cost remains $0.
