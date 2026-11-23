# RoadTalk public-beta privacy notice — review draft

Status: **draft for privacy/legal review; not approved public notice**

This draft translates RoadTalk's approved privacy principles into user-facing content for review. It is not legal advice and has not received legal-counsel approval.

## Data RoadTalk may process

Depending on features a user explicitly enables, RoadTalk may process account/device/session data, a public pseudonymous callsign/avatar, foreground location and derived coarse context, channel/convoy state, minimal push-to-talk authorization metadata, notification/moderation state, and privacy-safe operational logs.

Current approved scope does **not** include selling personal or sensitive data, using location for advertising, exposing exact coordinates to other users, or durable recording/storage of user audio/transcripts.

## Why data is used

Data is limited to authentication/security, user-requested communication, current location/proximity/route features, abuse prevention/moderation, notifications, reliability, and support/operations. A provider or SDK does not gain a broader purpose merely because it processes data on RoadTalk's behalf.

## Location and microphone

Foreground location and microphone access are feature-specific and revocable. RoadTalk must explain purpose before requesting permission and continue to fail closed when permission or current authorization is absent. Background location/audio is not implied by public-beta readiness and requires separate approval if ever added.

## Sharing and providers

RoadTalk should disclose approved infrastructure/service providers and the minimized data each receives before launch. Payment/store/premium providers remain disabled until separately approved. RoadTalk does not sell personal data.

## Retention and deletion

Retention is bounded by feature purpose and the reviewed retention schedule. Users must have a documented deletion path. Some deleted data may remain in encrypted backups until the disclosed backup-retention window expires; restored systems must reapply deletion obligations.

Exact public-beta retention periods and the final deletion request process are still pending review, so this draft is not publication-ready.

## Security and choices

RoadTalk uses least-privilege access, managed secrets, privacy-safe logging, dependency/container/IaC scanning, and explicit release gates. No system can promise absolute security. Users can withdraw feature permissions and should be able to request account deletion under the final documented process.

## Unresolved before publication

Final review must add the legal entity/contact, jurisdictions served, applicable rights/request process, exact retention periods, provider list/transfer disclosures, age/children treatment, effective date/change process, and any legally required state/country-specific notices.
