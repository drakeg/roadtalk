# Identity and recovery operations

## Scope and invariants

This runbook covers Sprint 2 callsign, bundled-avatar, and anonymous recovery
operations. It authorizes no email, SMS, password, social login, contact verification,
uploaded media, location, audio, analytics, or AWS service.

- Public identity contains only display callsign and bundled-avatar identifier.
- Callsign availability never identifies the owning account.
- Recovery is optional and proves possession of a high-entropy key, not a real-world
  identity.
- Raw recovery keys are returned once and are never available to operators.
- Invalid, unknown, and replayed keys share the same public failure.
- Successful recovery rotates the key and revokes prior sessions.
- There is no support, database, or administrator bypass for a lost key.

Use only synthetic callsigns and recovery keys in rehearsals. Never place either value
in tickets, chat, screenshots, shell history, logs, analytics, or retained evidence.

## Expected API operations

| Endpoint | Authentication | Expected behavior |
|---|---|---|
| `GET /api/v1/callsigns/availability` | Current session | Available/unavailable plus stable reason; no owner |
| `GET /api/v1/me/profile` | Current session | Private setup state plus minimal public identity |
| `PATCH /api/v1/me/profile` | Current session | Versioned atomic callsign/avatar update |
| `POST /api/v1/me/recovery-key` | Current session | Create/rotate and return plaintext once |
| `POST /api/v1/sessions/recover` | None; tightly rate-limited | Transfer eligible new device, revoke sessions, rotate key |

## Synthetic acceptance rehearsal

1. Register installation A and complete a synthetic callsign/avatar profile.
2. Check an available, unavailable, reserved, and malformed callsign. Record only
   status, stable reason/code, route template, request ID, and timestamp.
3. Submit a stale profile version and confirm `PROFILE_VERSION_CONFLICT` without
   recording the callsign.
4. Create a recovery key on A. Do not retain the value in evidence.
5. Register fresh installation B and recover the account with the key.
6. Confirm B receives the original account plus a replacement key, while A's prior
   session no longer authenticates.
7. Retry the consumed key and an unrelated synthetic key. Confirm both produce the
   same `RECOVERY_FAILED` status/body shape.
8. Exceed the approved synthetic rate-limit boundary. Confirm stable
   `RECOVERY_RATE_LIMITED` or `CALLSIGN_RATE_LIMITED` plus `Retry-After`, without
   publishing configured thresholds.
9. Inspect captured application output for only route templates and allowlisted
   technical fields. Search locally for the synthetic markers, then destroy the
   temporary output.
10. Delete the synthetic accounts/data through the approved disposable-test cleanup.

Evidence must not include request/response bodies for key creation or recovery.

## Diagnosis

Search by request ID, route template, time range, result class, HTTP status, and stable
problem code. Allowed examples include `/api/v1/sessions/recover`,
`RECOVERY_FAILED`, and `client_error`. Do not search by or request:

- callsign text;
- recovery key or selector;
- installation, account, device, or session identifier;
- authorization/refresh token;
- request body or concrete URL path.

The field-test API currently uses one worker and bounded in-process limiters. A restart
clears limiter memory. Do not restart merely to bypass a rate limit; diagnose abuse or
test configuration first. Multi-worker deployment requires a separately approved
shared-limit design and cost review.

## Lost key or recovery complaint

1. State that RoadTalk cannot retrieve or reset a raw key.
2. If the user still has an authenticated device, direct them to create a replacement
   key, which invalidates the predecessor.
3. If the user has neither an authenticated device nor the key, the anonymous identity
   is unrecoverable. Do not inspect hashes, change account ownership, or accept contact
   documents as proof.
4. Record only the generic outcome and policy reference—never a callsign, candidate
   key, or account identifier.

## Suspected key compromise

If an authenticated device remains available, rotate the account recovery key and
revoke affected devices/sessions. If broad pepper disclosure is suspected, follow
[Credential rotation](credential-rotation.md): changing the recovery pepper invalidates
all existing recovery keys and requires an explicit product-owner decision. Preserve
only privacy-filtered evidence.

## Cost and field-test boundary

All procedures use the existing API, PostgreSQL database, mobile application, and CI.
Expected incremental AWS cost is **$0**. This runbook does not enable Terraform or
authorize Cognito, SES, SNS, Pinpoint, Lambda, S3 avatar storage, RDS, managed cache,
NAT Gateway, load balancer, Fargate, or additional compute.

S01-E01 through S01-E03 remain hard blockers before field testing. Sprint 2 automated
evidence does not close them.
