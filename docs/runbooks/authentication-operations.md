# Authentication operations

## Behavior and privacy boundary

RoadTalk creates an anonymous account, device, and session. It collects an
installation identifier and platform plus generated security identifiers; Sprint 1
does not collect profile, location, proximity, channel, audio, or recovery data.
Access tokens last 15 minutes by default and remain only in mobile memory. Rotating
refresh credentials are stored in platform SecureStore and only their hashes are
stored by the API.

| Endpoint | Expected operation |
|---|---|
| `POST /api/v1/auth/anonymous` | Create account/device/session and token pair |
| `POST /api/v1/auth/refresh` | Consume and rotate one refresh credential |
| `GET /api/v1/auth/session` | Validate bearer token and active session |
| `POST /api/v1/auth/logout` | Revoke the current session |
| `DELETE /api/v1/auth/devices/{device_id}` | Revoke sessions for an owned device |

## Validation rehearsal

Use a local or disposable field-test installation; do not copy tokens into issue
comments or evidence.

1. Start from a cleared app SecureStore and register anonymously.
2. Confirm `/session` returns the expected account, device, and session identifiers.
3. Refresh once and confirm the returned refresh credential differs.
4. Reuse the consumed credential and confirm the family is rejected/revoked.
5. Register again, log out, and confirm that session no longer authenticates.
6. Register again, revoke its device, and confirm its sessions no longer authenticate.
7. Record only HTTP status, problem code, request correlation ID, and timestamps.

## Operational diagnosis

For an authentication incident, search privacy-filtered logs by a known correlation
ID and narrow time range. Never log or request authorization headers, access tokens,
refresh credentials, installation identifiers, database URLs, or request bodies.
Repeated `401` responses after a refresh failure should cause the client to clear its
local session and fail closed. A `409` registration conflict requires investigation;
do not delete accounts to make the symptom disappear.

Credential compromise or planned key changes follow
[Credential rotation](credential-rotation.md). Sprint 1 itself has no account
recovery or real-world identity proof. Sprint 2 adds only the optional anonymous,
key-based flow documented in
[Identity and recovery operations](identity-recovery-operations.md); it does not add
contact verification or an operator bypass.
