# Moderation report persistence and lifecycle

Sprint 12 D03 persists only the bounded report metadata approved by D02.

## Stored fields

A report stores identifiers for the report, authenticated reporter and subject account; one bounded reason; lifecycle state; a SHA-256 hash of the client idempotency key; terminal timestamp; version; and normal row timestamps.

It does not store report prose, attachments, audio, transcripts, raw location/route information, provider credentials, or arbitrary evidence payloads.

## Lifecycle

- New reports start as `submitted`.
- The same reporter/idempotency key and identical subject/reason returns the existing report.
- Reuse of the key for different report content fails with the same generic lifecycle error.
- Self-reporting, deleted/missing subjects and invalid transitions use the same non-enumerating error.
- Terminal states are `closed` and `withdrawn`; a terminal transition records `ended_at` and increments the version.
- Database constraints enforce bounded reason/state values, reporter/subject separation, idempotency-hash shape and state/timestamp consistency.

Account deletion cascades reports associated with that account, providing deterministic deletion behavior without preserving orphaned moderation evidence. Administrative moderation workflow is not introduced by D03.
