# Sprint 11 D08 convoy hardening

D08 hardens the existing convoy feature without broadening authorization or adding providers.

## Reliability and concurrency
- PostgreSQL enforces at most one active convoy membership per account with a partial unique index. UI/API pre-checks remain convenience only; the database is the concurrency boundary.
- Existing row locks continue to serialize membership termination and convoy disband operations.
- Awareness snapshots cannot outlive the viewer's expiring membership and continue to require active convoy, account, consent, current location and source-session state.

## Abuse and anti-enumeration
- Lifecycle conflicts return one normalized message instead of exposing whether a convoy, membership, or terminal state exists.
- Request schemas remain closed and bounded; convoy names remain capped at 64 characters.
- Join identifiers do not provide any listing/search endpoint. There is no cross-convoy member lookup or non-member awareness endpoint.

## Privacy and authorization
Convoy remains a narrowing/context mechanism only. Existing authentication, location consent/currentness, proximity, Same-road, channel and media-grant gates remain authoritative. No coordinates, route history, durable movement state, background location/audio, external provider, analytics, or recurring-spend dependency is introduced.

## Regression evidence
Persistence tests now correctly compare model column **names** when checking forbidden privacy fields; the prior object-vs-string assertion could not detect a forbidden column. Tests also cover the one-active-membership database invariant, normalized conflict output, and awareness lifetime bound.
