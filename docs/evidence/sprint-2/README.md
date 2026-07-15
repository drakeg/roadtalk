# Sprint 2 synthetic identity evidence

- Evidence type: automated tests plus repository inspection
- Synthetic-data rule: no real callsign, account, device, session, or recovery key
- Baseline: merge commit `1769e873262a3b932caaf3ff990923cd4325b199`
- CI: [run 29381798557](https://github.com/drakeg/roadtalk/actions/runs/29381798557)
- Field-test status: not performed

## S02-T11 lifecycle demonstration

The lifecycle is demonstrated as a composition of deterministic tests using
generated accounts, UUIDs, installation identifiers, callsigns, avatar identifiers,
sessions, and recovery secrets. Evidence records only test names and stable outcomes;
it does not retain generated secret or identity values.

| Lifecycle step | Automated evidence | Demonstrated outcome |
|---|---|---|
| Register anonymously | `test_anonymous_session_rotation_replay_and_device_revocation`; mobile `SessionClient` registration test | Account/device/session are created and the refresh credential is stored through SecureStore while the access token stays in memory. |
| Read incomplete identity | `test_missing_profile_is_private_and_conditionally_creatable`; `test_profile_is_optional_for_existing_accounts` | Existing anonymous accounts remain private and incomplete without invented public identity. |
| Validate and reserve callsign | `test_callsign_normalization_is_deterministic`; unsafe-policy and availability tests | Equivalent, invalid, reserved, confusable, and taken candidates fail with stable owner-free results. |
| Set callsign and avatar | `test_owner_profile_conditional_update_lifecycle`; mobile identity setup test | Owner performs an atomic versioned update using an active bundled avatar and completes setup. |
| Handle conflict and edit settings | stale-update/cooldown tests; mobile optimistic-conflict reload test | Stale writes fail closed, cooldown is bounded, and a refreshed version can be edited safely. |
| Render avatar catalog | backend/mobile catalog agreement and accessibility tests | Active choices render accessibly, retained retired choices remain renderable, and new retired/unknown selections fail closed. |
| Create recovery key | recovery security/service/route tests; mobile one-time-display test | A 256-bit secret is shown once; only a salted, peppered scrypt hash is persisted server-side. |
| Transfer to a new device | `test_recovery_transfer_rotation_replay_and_revocation`; mobile recovered-session test | Eligible fresh installation receives the account session, old sessions are revoked, and a replacement key is issued. |
| Reject replay/enumeration | recovery constant-shape, HTTP hardening, logging, and rate-limit tests | Invalid, unknown, and replayed keys share one response shape; attempts are bounded and secrets do not enter logs. |
| Revoke/logout | authentication integration and mobile logout tests | Revoked sessions fail and local credentials are cleared even when server logout is unavailable. |

## S02-T10 privacy and scope evidence

- Exact OpenAPI path/schema allowlists reject unapproved identity fields and routes.
- Public identity contains only callsign and bundled-avatar identifier.
- Closed-field structured logging rejects synthetic sensitive extras and uses route
  templates instead of concrete identifiers.
- Recovery UI and transport tests exclude ordinary storage, URLs, analytics,
  automatic clipboard behavior, and later-sprint permissions.
- `scripts/ci/check-identity-privacy.py` rejects cloud SDK, managed-cache, permission,
  storage, clipboard, and logging drift.
- Terraform remains disabled and plans zero resources by default.

## Privacy-safe reproduction

Use the normal repository test targets and the CI workflow. Do not paste generated
recovery keys, callsigns, bearer credentials, identifiers, request bodies, concrete
paths, or unrestricted logs into issues or evidence records. Record only the commit,
workflow run, test name, pass/fail state, and a redacted problem code when necessary.

## What this does not prove

This record does not claim a physical-device demonstration, native storage audit,
clean-machine rehearsal, enabled AWS plan, deployed field-test, or production-scale
rate limiting. Those remain outside Sprint 2 repository/CI evidence and are blocked
by S01-E01 through S01-E03 where applicable.
