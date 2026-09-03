# Sprint 9 D07 — Mobile notifications experience evidence

## Scope

S09-D07 implements S09-R09 / S09-T09 on the approved Sprint 9 notification contracts. The mobile app now exposes an authenticated RoadTalk inbox, account-owned ordinary notification preferences, read/dismiss state, and a tightly constrained urgent-alert compose/display experience.

## Acceptance evidence

- `mobile/src/notifications/api.ts` consumes only the existing authenticated notification APIs and validates the closed response contract before exposing it to the UI.
- `mobile/src/screens/NotificationsScreen.tsx` renders notification source, age, expiry, channel context, read/dismiss actions, preference controls, accessible live status, expired states, and deterministic degraded messaging.
- Urgent-alert presentation preserves the locked statements that RoadTalk is not an emergency service, delivery is not guaranteed, the alert is user-generated/unverified, and users must contact local emergency services directly when emergency assistance is needed.
- Urgent compose accepts only the message. The client generates the required idempotency key; recipient selection remains server-side and the UI exposes no recipient, coordinate, radius, route, corridor, or destination targeting controls.
- `mobile/src/__tests__/NotificationApi.test.ts`, `NotificationsScreen.test.tsx`, `NotificationScope.test.ts`, and the updated home-screen test cover contract parsing, stable errors, inbox/preferences/state/urgent flows, accessibility/navigation, sensitive-field rejection, and provider/dependency/privacy boundaries.

## Provider, permission, and cost boundary

This deliverable intentionally does **not** activate APNs, FCM, Expo Push, SNS, Pinpoint, Web Push, or another external notification provider. It adds no push-provider SDK or credential, no payment method, no AWS/LiveKit Cloud resource, and no incremental recurring cost.

The current mobile experience provides the RoadTalk in-app inbox while the application is open. It does not claim background or OS push delivery. No background location or background audio permission, task, or collection path is added for notifications.

## Known evidence limits

Real suspended/killed/offline/background notification delivery remains outside the approved provider-free boundary. Broad physical-device OS notification permission/presentation behavior also remains a named Sprint 9 evidence exception until a separately approved provider/device-validation step exists. These limits do not weaken the in-app inbox or server-side notification authorization contract.

## Merge gate

D07 is complete only when mobile type-check/tests and repository CI/hardening gates are green and the PR is merged. Merge closes issue #225 and unlocks S09-D08; it does not authorize any external provider, recurring spend, background location/audio, emergency-service integration, or guaranteed-delivery claim.
