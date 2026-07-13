# Credential rotation

## Controls

Rotate through an approved masked secret-entry mechanism. Never place a value in
Terraform variables, Git, CI inputs, tickets, chat, logs, deployment image layers,
or shell history. Record parameter name and version only. Take a verified database
backup before changing database credentials.

| Credential | Effect | Validation and rollback |
|---|---|---|
| Token signing key | Existing access tokens fail after API restart; refresh may issue new access tokens | Schedule a session interruption, update parameter, redeploy, register/refresh/session test; restore prior parameter version and redeploy if needed |
| Refresh-token pepper | All stored refresh hashes become unusable | Treat as global logout, update parameter, redeploy, verify old refresh fails and new registration works; rollback only during the controlled window |
| PostgreSQL password / `DATABASE_URL` | API and maintenance access can fail | Change database role password and both parameters as one maintenance operation; readiness and migration check must pass; revert both sides together |
| AWS human/automation credential | May block Terraform or deployment | Prefer temporary role credentials; validate identity and least privilege before retiring the old credential |

`ROADTALK_TOKEN_SIGNING_KEY` currently supports one active key, not overlapping key
IDs. Therefore a signing-key rotation deliberately invalidates access tokens for at
most their configured TTL (15 minutes by default). Changing the refresh pepper is a
deliberate global logout. Communicate both impacts before proceeding.

## Rotation procedure

1. Open a change record with reason, owner, scope, window, expected session impact,
   validation, and rollback criteria.
2. Verify the target AWS account/region and current application commit; take a
   database backup when applicable.
3. Generate a unique high-entropy value in the approved secret manager and create a
   new SecureString parameter version under `/roadtalk/field-test/`.
4. Redeploy the same immutable image so the root-only runtime environment is rebuilt;
   do not edit `runtime.env` manually.
5. Verify live, ready, version, anonymous registration, refresh, session validation,
   logout, and privacy-safe logs.
6. Observe for one access-token TTL. If healthy, revoke/delete the superseded secret
   according to the credential provider and close the record.
7. On failure, restore the recorded prior parameter version, redeploy the same image,
   validate, and escalate before making another change.

For suspected compromise, revoke the credential immediately where safe, rotate all
dependent values, preserve privacy-filtered audit evidence, and assume exposed
session credentials are invalid. Do not delay containment solely to preserve client
sessions.

## Review rehearsal

Before field testing, two reviewers walk through target verification, masked value
entry, signing-key and pepper impact, atomic database change, redeployment,
validation, rollback, and evidence fields. The rehearsal must not use a real secret.
