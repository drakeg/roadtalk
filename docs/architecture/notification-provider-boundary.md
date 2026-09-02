# Notification provider boundary

Sprint 9 D05 introduces only a deterministic local/CI delivery-provider boundary. It does not activate push delivery.

## Allowed implementations

- `DisabledNotificationProvider` is the default fail-closed provider.
- `FakeNotificationProvider` is deterministic and may be used only in local/test environments.
- `build_notification_provider()` rejects fake delivery outside local/test and has no real-provider option.

There is no APNs, FCM, Expo Push, SNS, Pinpoint, Web Push, SMS, email, queue, worker, provider account, URL, API key, token, credential, SDK, or network request in this deliverable.

## Request contract

The server-internal delivery request contains only the persisted notification ID, recipient account ID, closed notification class/priority, and issue/expiry timestamps. It deliberately excludes device IDs, push tokens, message text, coordinates, radius, route/corridor data, destination, provider references, and targeting overrides.

Authorization happens before this boundary. A provider never selects recipients and cannot turn an authorization denial into a delivery candidate.

## Result contract

Provider results are limited to the notification ID, `accepted` or `disabled` status, bounded provider version, attempt timestamp, and original expiry timestamp. `accepted` means only that the deterministic provider boundary accepted the request. It does **not** mean a human received, read, acknowledged, or responded to the notification.

`NotificationDeliveryBoundary` enforces a bounded timeout, matching notification ID, matching expiry, current timestamps, and sanitized `notification delivery unavailable` failure semantics. Expired requests fail closed.

## Activation boundary

A real provider requires a later explicit product, privacy, security, cost, credential, rollback, and operational decision. Sprint 9 D05 does not authorize one and keeps incremental recurring cost at $0.
