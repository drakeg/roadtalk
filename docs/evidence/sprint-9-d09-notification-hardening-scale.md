# Sprint 9 D09 — Notification hardening, scale, and compatibility evidence

## Scope

S09-D09 covers S09-R11 / S09-T11. It hardens the approved in-app/local notification implementation without activating an external push provider, provider credentials, background location/audio, marketing analytics, paid infrastructure, or production/public-beta behavior.

## Dedicated hardening gate

`scripts/ci/check-notification-hardening.py` is enforced by the existing CI security job. The gate fails if notification code or dependencies introduce:

- APNs, FCM/Firebase, Expo Notifications, OneSignal, Web Push, Pinpoint, or similar external push-provider integration;
- provider API keys, private/server keys, push/device/registration tokens, credential JSON, or external notification network clients;
- backend/mobile push SDK dependencies that would broaden the approved provider-free boundary;
- background location/audio permissions or update APIs;
- Segment, Mixpanel, Amplitude, or equivalent marketing-analytics activation;
- removal of the existing prohibited sensitive/targeting field contract; or
- removal of D09 CI enforcement.

The existing Sprint 9 privacy gate remains active in the same workflow, along with Sprint 5–8 authorization, privacy, hardening, scale, mobile, dependency, container, and IaC regressions.

## Synthetic migrated scale matrix

`backend/tests/test_notification_scale.py` runs against the migrated disposable CI database and fixes the named matrix before the evidence run at:

- 100 registered accounts;
- 25 potential recipients;
- 10 urgent-alert publishers;
- 5 of the 25 potential recipients opted out, proving notification preferences can narrow but not widen the authorization-derived audience;
- external push provider disabled; and
- incremental recurring cost: $0.

The p95 target was locked before the named evidence run at **1,500 ms** for the complete server-side compose operation for one publisher: current sender/session/channel authorization, supplied already-authorized candidate set, notification-preference narrowing, idempotency protection, and in-app notification persistence for the eligible recipients.

### Named evidence result

Pending the first green D09 CI evidence run. This section will be updated with the emitted `Notification synthetic scale` metrics before D09 is marked ready for merge.

## Compatibility/evidence boundaries

Automated evidence in D09 covers the server-side in-app notification path, local/test fake-or-disabled provider boundary, database migration compatibility, mobile TypeScript/API/UI regressions, and repository CI on GitHub-hosted Linux runners.

The following evidence is explicitly **not performed or claimed** in D09:

- physical iOS device push delivery;
- physical Android device push delivery;
- physical/browser OS notification delivery while suspended or offline;
- APNs, FCM, Expo Push, SNS, Pinpoint, Web Push, or any real external push-provider delivery;
- provider credential provisioning/rotation;
- emergency-services/public-safety integration;
- guaranteed delivery, human read, or human response; and
- production/public-beta scale or multi-worker distributed rate-limit behavior.

Those unperformed cases remain explicit exceptions rather than inferred coverage from the automated in-app/local evidence.

## Cost and activation boundary

D09 adds no payment method, paid plan, recurring service, AWS/LiveKit Cloud activation, external push-provider account, push-provider credential, background location/audio capability, or marketing analytics service. Current and incremental recurring cost remain **$0**.

## Merge gate

D09 is complete only after the named scale result is recorded here and CI, Sprint 7 hardening, Sprint 8 hardening, and Sprint 9 planning/hardening gates are green. Merge closes issue #227 and unlocks D10 only; it does not authorize Sprint 10 or any external provider/production activation.
