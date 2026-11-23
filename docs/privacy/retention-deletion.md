# Retention and deletion preflight

Status: **technical draft pending final policy/legal review**

This document reconciles RoadTalk's existing privacy model, data model, backup controls, and feature-specific lifecycle rules into a public-beta review matrix. It is not a final privacy-policy promise.

| Data class | Current technical intent | Deletion / expiry behavior | Public-beta review status |
| --- | --- | --- | --- |
| Precise/current location | Current feature state only; no advertising use; no other-user exact coordinates | Withdraw/pause/logout/account lifecycle invalidates current location paths; exact retention remains feature-scoped | Technical behavior documented; final policy wording pending |
| Presence / route context | TTL/current-only where implemented | Expires or is invalidated by lifecycle/authorization changes | Technical behavior documented |
| Audio/transcripts | Audio recording/transcript storage is not part of current approved scope | No durable audio/transcript record to delete in current scope | Must remain true unless separately approved |
| Media/PTT grants and minimal metadata | Minimal security/quality metadata; historical design target up to 30 days pending review | Expiry/revocation plus bounded record lifecycle | Final retention period must be approved before launch |
| Sessions/devices/security records | Active lifecycle plus bounded security needs | Revocation/logout/account lifecycle removes active authority | Final post-deletion security retention must be approved |
| Consent history | Evidence while account exists and only as legally/operationally required afterward | Account deletion must remove or minimize data except a justified retained record | Final legal/retention basis pending |
| Notifications/moderation state | Bounded feature-specific TTL/retention | Expiry, dismissal/revocation, account cascade where designed | Verify final production defaults before launch |
| Application logs | Privacy-safe logs; architecture target historically 30 days in production | Log lifecycle removes expired data; no precise location/tokens | Final production period pending approval |
| Backups | Encrypted, bounded lifecycle; current production contract requires explicit retention | User deletion may persist in backups until backup expiry; restored data must reapply deletion obligations | Disclosure and final period pending review |

## Account deletion requirements

Before public beta, RoadTalk must have a tested account-deletion path or an explicit supported deletion request workflow that:
- revokes active sessions, devices, media authority, and current location/presence state;
- deletes or irreversibly de-identifies user-owned application data except records with a documented retention basis;
- records no secret, recovery key, exact location, or unrelated-user payload in deletion evidence;
- documents backup-remanence timing and reapplies deletion after any restore;
- provides a verifiable completion result without exposing internal identifiers.

## Retention decisions still required

The public-beta policy must finalize exact periods for security records, PTT/media metadata, logs, consent evidence after deletion, notification/moderation records, and backups. Any retained post-deletion data needs a purpose, owner, duration, access boundary, and deletion mechanism.

Until that review is complete, the D08 contract keeps public-beta readiness false.
