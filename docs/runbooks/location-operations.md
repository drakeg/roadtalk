# Foreground location operations

## Scope and invariants

This runbook covers Sprint 3 foreground consent, current-location submission,
coarse nearby status, expiry, pause, withdrawal, and privacy-safe diagnosis. It does
not authorize field testing, background location, maps, location history, or any new
AWS or third-party service.

- The client requests only foreground/when-in-use permission after explaining why.
- Collection runs only while the authenticated location experience is foreground-active.
- PostgreSQL stores at most one expiring current row per account; there is no route,
  breadcrumb, presence, analytics, or history store.
- Exact coordinates, accuracy, heading, speed, source identifiers, and derived
  movement are private inputs. They must not appear in tickets, screenshots, logs,
  URLs, traces, crash fields, analytics, or retained evidence.
- Nearby output is limited to availability, `none`/`few`/`many`, freshness, and the
  caller's expiry boundary. Never diagnose by asking for another user's identity,
  coordinates, exact distance, bearing, or exact nearby count.
- Expired or unusable rows are ineligible immediately. Physical cleanup is idempotent
  and is not required for correctness.

## Approved API operations

| Endpoint | Purpose | Safe evidence |
|---|---|---|
| `PUT /api/v1/me/location-consent` | Grant current foreground policy | Status, stable code, route template, request ID, time |
| `DELETE /api/v1/me/location-consent` | Withdraw consent and current row | Same metadata; no body capture |
| `PUT /api/v1/me/location` | Replace current sample | Status and receipt field names only; no values |
| `DELETE /api/v1/me/location` | Pause and remove current row | Status, stable code, route template, request ID, time |
| `GET /api/v1/nearby/summary` | Read caller-relative semantic status | Status and semantic bucket only when synthetic |

## Synthetic acceptance rehearsal

Use only generated coordinates and accounts in an isolated test database. Do not use
a real address, current device position, callsign, account identifier, or production
credential.

1. Authenticate synthetic installation A and grant the current foreground policy.
2. Submit one policy-valid synthetic sample, then a newer replacement. Confirm only
   one current row remains and the response contains no submitted location values.
3. Exercise malformed, stale, future, inaccurate, out-of-order, and implausible
   samples. Confirm stable `409`/`422` problems without submitted values or policy
   thresholds.
4. Create synthetic installation B within the test radius and confirm only a semantic
   nearby bucket is returned. Test empty, self-only, outside-radius, expired,
   degraded, and withdrawn candidates.
5. Exceed synthetic mutation and nearby-read limits. Confirm `429`, a bounded
   `Retry-After`, and no configured threshold disclosure.
6. Pause location twice and verify idempotent deletion. Resume, withdraw consent, and
   verify the row is removed. Delete the synthetic account and verify cascade removal.
7. Advance the test clock through expiry. Verify nearby reads fail closed before and
   after idempotent expired-row cleanup.
8. Drive mobile fake clocks through background, navigation exit, logout, pause,
   native-watch failure, and unmount. Confirm subscriptions, polling, timers, and
   process-memory location state stop and clear.
9. Run the full backend, migration, mobile, security, container, dependency, and
   credential-free zero-resource Terraform gates.
10. Search transient test output for the synthetic markers, record only the gate
    result, then destroy the temporary output and synthetic data.

Physical-device permission, battery, OS-native storage, and lifecycle evidence remain
pending behind S01-E01. Do not represent synthetic tests as physical-device evidence.

## Diagnosis

Search only by request ID, route template, time window, result class, HTTP status, and
stable problem code. Approved examples include `/api/v1/me/location`,
`LOCATION_UNAVAILABLE`, and `LOCATION_RATE_LIMITED`.

Do not request or search by coordinate, accuracy, heading, speed, callsign, account,
device/session identifier, concrete URL, request body, or database row contents. If
those values appear in operational output, treat it as a suspected privacy incident:

1. stop collection and restrict access to the affected output;
2. do not copy the sensitive material into a ticket or chat;
3. preserve only access-controlled, privacy-filtered incident metadata;
4. notify the product owner and follow the P0/P1 location-disclosure response in the
   threat model;
5. correct the leak and rerun the location privacy gate and synthetic corpus before
   resuming work.

The field-test API intentionally uses one worker and process-local limits. Restarting
clears limiter state; never restart merely to bypass a rate limit. A shared limiter or
multi-worker deployment requires a separate architecture and cost decision.

## Cost boundary

This procedure adds **$0 incremental AWS cost** and uses existing CI/local PostGIS.
If the already-designed field-test stack is later enabled, the current expected total
is approximately **$20–$23/month after the temporary EC2 promotion**, before tax and
heavy traffic. This runbook does not authorize enabling Terraform, RDS, Redis, NAT
Gateway, a load balancer, maps/geocoding, analytics, a scheduler, or extra compute.
