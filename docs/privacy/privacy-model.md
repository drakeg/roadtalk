# RoadTalk Privacy Model

- Status: Approved baseline
- Issue: #14
- Requirements: S00-R10
- Acceptance: S00-T08
- Date: 2026-07-12

## Principles

- collect the least data required for an active feature
- request foreground access before considering background access
- separate microphone, foreground location, background location, notifications, terms, and privacy consent
- make collection visible, understandable, revocable, and deletable
- never use location for advertising
- never sell personal or sensitive data
- treat callsigns as public pseudonyms and keep account/security fields private
- keep recovery material out of logs, analytics, URLs, support workflows, and
  ordinary device storage
- do not record audio in Sprints 1–5
- do not expose exact coordinates to other users
- treat SDK/provider behavior as part of RoadTalk's responsibility

## Data inventory

| Category | Purpose | Precision/content | Storage | Access | Initial retention |
|---|---|---|---|---|---|
| Account/device/session | Security and continuity | Opaque IDs, credential hashes, platform/version | PostgreSQL/secure device storage | User and authorized service | Active life; limited security record after revocation |
| Public profile | Display callsign and bundled-avatar identifier | User-selected | PostgreSQL; avatar assets bundled with app/API image | Other eligible users | Until changed/deleted |
| Recovery credential | Random selector plus salted, peppered scrypt hash | No contact PII; plaintext returned once | PostgreSQL hash; optional explicit device-only SecureStore copy | Account owner and recovery service | Until rotated or account deleted |
| Current location | Proximity authorization | Exact sample server-side; no client disclosure | One current PostGIS row | Proximity service only | Replaced/expired quickly |
| Location history | None for MVP | Not collected | None | None | None |
| Presence/channel | Delivery eligibility | State and expiry | Redis/PostgreSQL context | Authorized service | TTL; remnants within 24h |
| Live audio | Realtime communication | Audio track | In transit through LiveKit | Eligible participants | Not recorded/stored |
| Media metadata | Security/quality | Times, opaque refs, aggregate quality | PostgreSQL/log metrics | Restricted operations | Target 30 days |
| Push token | Notifications | Provider token | Encrypted/reference | Notification service | Until revoked/replaced |
| Logs/metrics | Reliability/security | Allowlisted technical fields | CloudWatch | Restricted operations | 14 days field test; 30 days production target |
| Backups | Recovery | Encrypted database snapshot | S3/RDS | Recovery operators | 7 days field test; disclosed production window |
| Reports/moderation | Later sprint | Not implemented in MVP Sprints 1–5 | None initially | None | Defined in Sprint 12 |

## Consent sequence

1. Explain RoadTalk's nearby communication purpose without requesting permission.
2. Create the minimum anonymous account/session.
3. Request microphone only when the user enters or activates radio functionality.
4. Request foreground location with a clear feature explanation.
5. Demonstrate foreground operation before separately offering background location.
6. Request background access only when a user enables a feature that truly needs it.
7. Record disclosure/policy versions and choice timestamps.
8. Provide settings to pause presence, withdraw location, revoke microphone behavior, manage notifications, and delete the account.

Denial must leave the app stable and explain which capability is unavailable. It must not repeatedly coerce the user.

## Location rules

- foreground is the default
- background collection is opt-in and independently revocable
- sample frequency adapts to movement and active use
- reject unnecessary precision and stale/inaccurate samples
- nearby users receive counts/status, not coordinates or distance precise enough to locate someone
- no historical trip route in MVP
- no location in analytics, crash messages, URLs, push payloads, or routine logs
- deleting/withdrawing location removes current data and presence eligibility promptly

## Audio rules

- transmit only while the user intentionally holds/activates the approved PTT control
- visible and accessible transmitting state
- no ambient/background recording outside explicit PTT behavior
- no server recording, transcription, summaries, translation, or AI until later approved sprints and new consent/privacy review
- Bluetooth, route, interruption, and screen-lock behavior must not produce unintended capture
- technical quality metrics exclude content

## User controls

- create or rotate an optional anonymous recovery key
- choose whether the newly displayed key is written to device-only SecureStore
- edit callsign and select only an approved bundled avatar
- pause/leave radio
- foreground-only versus separately approved background mode
- current channel
- microphone/location/notification guidance linking to OS settings
- blocked/muted users when implemented
- active devices/sessions and revocation
- export of meaningful account/profile/consent data before production
- account deletion with status and completion notice

## Deletion

1. authenticate or verify the deletion request
2. revoke sessions, devices, recovery credentials, push tokens, presence, and media grants
3. remove current location immediately
4. prevent account reuse during processing
5. delete/anonymize profile, account, metadata, and object storage according to policy
6. allow encrypted backups to age out within the disclosed maximum window
7. preserve only narrowly justified security/legal records, disconnected from public identity where possible
8. record completion without retaining deleted content

## Provider/SDK review

Before adding an SDK:

- inventory its collection, storage, transfer, subprocessors, and defaults
- disable advertising/tracking behavior
- ensure App Store/Play disclosures match actual behavior
- document deletion and incident paths
- pin/version-review the dependency
- reject SDKs that require unrelated sensitive data

## Sprint 2 identity and recovery rules

- The only public identity fields are display callsign and bundled-avatar identifier.
  Account, device, session, recovery, setup, and moderation fields remain private.
- Callsign availability returns only available/unavailable with a stable reason and
  never identifies the owner.
- Raw recovery keys exist only in the creation/recovery request and immediate success
  response. The server stores no plaintext copy and cannot retrieve one for support.
- Invalid, unknown, and replayed recovery keys share one response. Successful recovery
  rotates the key and revokes prior sessions.
- Mobile recovery state is transient by default. SecureStore is off by default,
  requires explicit user choice, and uses a device-only accessibility class.
- A lost recovery key has no administrative bypass. The existing authenticated device
  remains authoritative; without it or the key, the anonymous identity is unrecoverable.
- Sprint 2 adds no location, audio, contacts, uploaded media, analytics, email, SMS,
  hosted identity provider, or cloud storage service.

## Store-policy baseline

Google Play requires transparency for user data and treats background location as sensitive: it must be central to the app, strongly justified, explicitly consented, and minimized. Android foreground-service declarations and demonstrations are required where applicable. Apple permission strings and privacy disclosures must accurately describe collection and use.

## Acceptance result

Every data category has a purpose, content/precision, storage, access scope, and retention baseline. Location and audio flows are covered from collection through withdrawal/deletion. Exact legal wording remains a pre-launch legal review, not an architectural omission.

## References

- [Google Play User Data policy](https://support.google.com/googleplay/android-developer/answer/10144311)
- [Google Play sensitive permissions/background location](https://support.google.com/googleplay/android-developer/answer/16558241)
- [Android foreground-service declarations](https://support.google.com/googleplay/android-developer/answer/13392821)
- [Expo Permissions](https://docs.expo.dev/guides/permissions/)
- [Expo Location](https://docs.expo.dev/versions/latest/sdk/location/)
- [Expo Audio](https://docs.expo.dev/versions/latest/sdk/audio/)
- [OWASP MASVS Privacy](https://mas.owasp.org/news/2024/01/18/masvs-v210-release--masvs-privacy/)
