# Notification persistence and preferences

Sprint 9 stores only the minimum state needed for ordinary notification preferences
and an authenticated account inbox.

## Ownership and lifecycle

- Each account may own one preferences row. Missing rows resolve to enabled defaults.
- Each notification belongs to exactly one account and is inaccessible through
  another account's routes.
- Preference and notification rows are deleted with the owning account.
- Inbox reads delete expired rows, omit dismissed rows, and return at most 50 current
  items in newest-first order. Correct retention does not depend on a worker.
- Read, dismiss, and preference changes use positive versions. The immediately prior
  request can be replayed only when the requested state already matches.

## Stored fields

Notification rows contain class, priority, semantic source, bounded display copy,
optional channel label, issue/expiry times, read/dismiss times, and a version. They do
not contain usernames, credentials, recovery keys, recipient lists, installation or
device identifiers, provider references or tokens, coordinates, distances, routes,
destinations, or location history.

Urgent alerts persist only their bounded user-generated message and common metadata.
The API reconstructs the fixed `verified=false`, `emergency_service=false`,
`delivery_guaranteed=false`, and safety statements from the versioned contract. This
keeps the safety invariant exact without creating mutable or duplicated safety copy.

## API boundary

All routes require the current authenticated session and derive account ownership
server-side. Requests contain only the two ordinary preference flags plus an expected
version, or a read/dismiss state plus an expected version. Responses expose semantic
notification fields only and never reveal delivery audience, provider state, precise
location, or internal authorization detail.

This deliverable adds no push provider, background worker, queue, cache, cloud
resource, external call, or recurring cost.
