# Administrator operations

RoadTalk administrator authorization is an explicit account role stored separately from normal registered-account authentication. A normal authenticated account receives HTTP 403 from every `/api/v1/admin/*` route.

## Bootstrap the first local administrator

Create or log in to a registered account first and copy its account UUID from the authenticated account/session UI or API. From the backend container/environment, run:

```sh
python -m scripts.set_admin <account-uuid>
```

Revoke the role with:

```sh
python -m scripts.set_admin <account-uuid> --revoke
```

This command changes only the local RoadTalk database. It does not create a hosted identity provider, external account, cloud resource, provider credential, or recurring cost. Do not grant administrator authorization to anonymous accounts.

## Browser console

An authorized administrator can open `/admin`. The console provides bounded account search and shows only support-safe fields: account UUID, status/type, call sign, device count, and active-session count.

Account disable/enable and account-session revocation require an explicit browser confirmation and a request body containing `{"confirm": true}`. Disabling an account revokes its current sessions before the transaction completes. Administrator mutations create minimal `admin_audit_event` records containing actor account UUID, target account UUID, action, and timestamp.

The console and API never expose passwords or password hashes, recovery keys, raw location/history, media/provider secrets, or callsign reassignment controls. There is no administrator bypass for stealing or reassigning a call sign.
