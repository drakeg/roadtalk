# Mobile

Current owner: S04-D06 mobile hold-to-talk experience. The retained identity,
recovery, and foreground-location flows were delivered by S02-D05–D08 and S03-D05–D07.

This directory contains the Expo/React Native/TypeScript development-build application.

## Current foundation

The current application provides:

- Expo SDK 57 with React Native 0.86 and the New Architecture
- iOS and Android development-client configuration
- typed public API endpoint configuration
- accessible native-stack navigation shell
- application-level error boundary with retry behavior
- Jest and React Native Testing Library smoke tests
- anonymous device registration and session bootstrap
- refresh credentials stored only through Expo SecureStore
- access credentials held only in process memory
- refresh rotation, logout, device revocation, and fail-closed recovery
- a versioned, code-native bundled avatar catalog with accessible labels
- retained rendering metadata for retired avatar identifiers
- accessible callsign setup and settings editing with availability checks
- bundled-avatar selection, optimistic conflict handling, and offline retry
- no downloaded or user-uploaded avatar media
- explicit recovery-key creation/rotation with one-time display
- account transfer on a newly registered device with replacement-session handling
- recovery keys transient by default and SecureStore-only after explicit opt-in
- purpose-before-permission foreground location onboarding
- foreground-only location sampling with bounded private updates
- lifecycle stops on pause, background, logout, screen exit, and unmount
- precise and approximate/reduced-accuracy permission support
- owner-only, non-authoritative accuracy, heading, speed, and freshness display
- semantic `none`, `few`, or `many` nearby awareness with no identity or exact value
- bounded nearby polling that stops with the foreground location lifecycle
- purpose-before-permission microphone onboarding with denied, blocked, unavailable,
  retry, and settings guidance
- pinned LiveKit Expo development-build dependencies behind a fakeable room adapter
- receive-only room join and remote-audio subscription with microphone capture off
- accessible press-and-hold authorization, transmission, receiving, busy, degraded,
  reconnecting, permission-denied, and error states
- server-authorized microphone-only publication with a deterministic 30-second maximum
- capture-off-first release, background, screen-exit, logout, reconnect, and failure
  ordering, including rapid press/release and cancellation races
- deterministic room, audio-session, and grant cleanup on every lifecycle exit

## Microphone and hold-to-talk media

Authenticated users can open **Microphone and live audio** and review the purpose,
storage limits, and receive-ready behavior before the operating-system prompt. The
prompt is requested only after **Enable live audio**. The user can continue without
audio, retry a denial, or open device settings after the platform blocks another
request.

The controller joins only after the app, screen, and authenticated session are active.
It accepts only a server response scoped to `join` and `subscribe` with no allowed
track sources. The LiveKit adapter starts a foreground audio session, subscribes to
remote audio, reports whether a remote participant is speaking, and explicitly keeps
the local microphone disabled while receive-ready.

Pressing and continuing to hold the large push-to-talk control requests a nested
transmit grant for the active receive grant. The client rejects any response that is
not exactly `publish` plus `microphone`; capture starts only after this authorization
returns. Release disables capture before revoking the transmit grant. The same
capture-off-first ordering applies to the 30-second maximum, backgrounding, screen
exit, logout or revocation, reconnect, connection failure, and unmount. Microphone
operations are serialized so a release cannot be overtaken by an in-flight native
enable call.

The control provides changing screen-reader labels, text and symbol cues that do not
depend on color, and a 112-point minimum touch target. Busy, provider-degraded,
authorization-error, permission-revoked, receiving, and reconnecting outcomes remain
explicit and fail closed. There is no toggle, hands-free, background-transmit,
proximity, or channel-selection mode.

The Expo configuration uses a RoadTalk-owned audio-only WebRTC plugin because the
generic plugin requests camera, overlay, and wake-lock capabilities that this sprint
forbids. Resolved iOS and Android prebuilds contain the purpose-accurate microphone
description and foreground audio permissions only; camera, screen sharing, background
audio services, wake lock, and overlay permissions are absent or explicitly blocked.
This requires an Expo development build and is not claimed to work in Expo Go.

No LiveKit project, provider credential, AWS resource, recording, transcription,
egress, or paid feature is created or enabled. Current and incremental recurring cost
remain **$0/month**. The activation projections remain those approved in the Sprint 4
readiness record: LiveKit Build can remain $0 within its documented caps; a bounded
AWS test window is planned at roughly $4–$6 in an active month; no activation or spend
is authorized by this deliverable.

## Foreground location lifecycle

Authenticated users can open **Location privacy** and review RoadTalk's purpose and
limits before the application asks the operating system for permission. The platform
prompt is requested only after the explicit **Enable location** action. Denial,
blocked/settings, unavailable-service, approximate/reduced-accuracy, retry, and pause
states remain usable and accessible.

The controller uses the pinned `expo-location` dependency only while the location
screen, application, and authenticated session are all active. Samples are sent in
JSON through the existing authenticated transport at a bounded cadence with an
in-memory monotonic sequence. Pause and lifecycle exits stop the native subscription;
when authentication is still available, they also ask the API to remove the current
short-lived row. Coordinates and sequences are never written to device storage,
placed in URLs, or logged.

Expo configuration enables iOS when-in-use and Android coarse/fine permissions only.
Background location flags remain false. There is no background task, foreground
service, geofence, motion permission, map SDK, analytics SDK, paid location provider,
or new AWS resource. The Sprint 3 mobile experience therefore adds $0 expected AWS
cost.

## Location and nearby experience

After a private sample is accepted, the screen may show the owner the device's local
accuracy, heading, and speed. These values are explicitly informational rather than
authoritative. Missing sensor values say **Unavailable**, old device samples say
**Stale**, and no movement value is inferred when the platform does not provide one.

The client reads `/nearby/summary` only after a successful private location update and
at a bounded 30-second cadence while the location screen remains foreground-active.
The response is reduced to **No**, **Some**, or **More** nearby RoadTalk activity from
the server's `none`, `few`, or `many` bucket. The UI never receives or displays a
candidate identity, exact count, coordinate, distance, or bearing. Missing caller
location, transient failure, and expired status remain distinct and retry safely.

Nearby timers and local freshness timers stop on pause, background, screen exit,
logout, and unmount. All state is process-memory-only and is cleared on lifecycle exit.

## Avatar catalog

`src/identity/avatarCatalog.json` is the mobile catalog contract. Active entries are
available for selection. Retired entries remain bundled so an existing public identity
continues to render, but the backend rejects new retired selections. `AvatarBadge`
groups each local glyph and palette into one screen-reader image with a descriptive label.

Catalog changes must preserve existing identifiers and synchronize with the backend
contract test. User uploads, remote image URLs, object storage, and image-processing
services are outside Sprint 2.

## Identity setup and settings

Authenticated users can open **Identity settings** without enabling any later-sprint
feature. The same screen handles first-time setup and later edits:

- callsigns receive local shape validation and an authenticated server availability check;
- the UI discloses that callsigns are public pseudonyms;
- only active bundled avatars can be selected, while a retained retired avatar still renders;
- saves use the current profile version and require a reload after a conflict;
- loading, availability, save, offline, cooldown, and retired-avatar errors remain retryable;
- controls include screen-reader roles, labels, live status updates, and 48-point targets.

The client holds access tokens only inside the existing session client. Identity requests
reuse its bearer transport and perform at most one refresh-and-retry after a 401.
No callsign, account identifier, token, or request body is logged or stored by this flow.

## Anonymous recovery

Authenticated users can open **Account recovery** to create or rotate an optional
high-entropy key. The key is displayed only in the immediate success state. Closing
that state removes it from application memory; it cannot be retrieved from the server.
The screen does not copy the key, place it in a URL, log it, analyze it, or write it to
ordinary storage.

Platform SecureStore persistence is off by default and occurs only when the user turns
on **Save in secure storage** before creating or recovering. That copy is
device-only and is not a substitute for keeping a private external copy for a new
device. Creating or successfully using a key invalidates its predecessor.

A newly registered device may submit a key through the JSON request body. Success
replaces the temporary session, stores only the replacement refresh credential through
the existing session storage boundary, revokes older sessions server-side, and displays
the rotated key once. Invalid, unknown, and replayed keys share one user-facing failure
message; rate limits expose no configured threshold.

## Setup

Node.js 24 and npm are used for the current Expo SDK.

```sh
cd mobile
npm ci
cp ../.env.example ../.env  # if the root local environment is not configured
npm run doctor
npm run typecheck
npm test
```

Set `EXPO_PUBLIC_API_BASE_URL` for the device running the development build:

- iOS simulator: `http://localhost:8000/api/v1`
- Android emulator: `http://10.0.2.2:8000/api/v1`
- physical device: `http://<development-machine-LAN-IP>:8000/api/v1`

Only `EXPO_PUBLIC_` values may be embedded in the application, and they must never contain secrets.

## Development builds

```sh
npm run ios
npm run android
npm start
```

The native commands create local iOS/Android development projects and run the Expo development client. Expo Go is not the required project runtime.

## Physical-device acceptance

Before a field test:

1. install a development build on one supported iOS target and one supported Android target;
2. confirm the RoadTalk foundation screen launches;
3. confirm the diagnostics screen shows the intended API URL;
4. verify text scaling, screen-reader labels, button target size, light/dark system behavior, and error fallback;
5. confirm no permission is requested before **Enable location** is selected;
6. exercise precise and approximate/reduced permission, denial, blocked/settings,
   disabled services, pause, background/foreground, screen exit, logout, and unmount;
7. confirm only foreground/when-in-use location is requested before entering the
   microphone screen and no notification, motion, background-location, or tracking
   permission appears;
8. observe that sampling stops on every lifecycle exit and assess battery behavior.
9. verify available/unavailable heading and speed, accuracy, current/stale state, and
   each semantic nearby bucket without any identity, exact count, distance, or bearing;
10. confirm nearby polling stops on pause, background, screen exit, logout, and unmount.
11. confirm no microphone prompt appears before **Enable live audio**, then exercise
    granted, denied, blocked/settings, unavailable, and changed-in-settings states;
12. confirm receive-ready plays permitted remote audio without starting capture and
    disconnects on background, screen exit, logout/revocation, failure, and unmount;
13. verify remote speaking, authorizing, transmitting, busy, degraded, reconnecting,
    permission-revoked, 30-second maximum, rapid press/release, and cancellation states;
14. confirm capture begins only after server authorization and turns off before grant
    cleanup on release, background, screen exit, logout, reconnect, and failure;
15. verify screen-reader double-tap-and-hold/release behavior, dynamic text,
    non-color cues, large text, and the push-to-talk touch target;
16. inspect the built manifests for no camera, background-audio service, wake lock,
    overlay permission, screen share, recording, or transcription capability.

These physical-device permission, battery, native-storage, and lifecycle checks remain
pending until the inherited S01-E01 hardware evidence gate is closed. Automated tests
use synthetic samples and do not claim real-device evidence.

## Credential-storage verification

The client intentionally has no AsyncStorage dependency. Before field testing:

1. inspect iOS Keychain and Android Keystore-backed SecureStore behavior on development builds;
2. verify raw access and refresh credentials do not appear in logs, screenshots, URLs,
   errors, analytics, ordinary files/preferences, or unencrypted backups;
3. rotate refresh credentials and confirm the old value is replaced;
4. log out and revoke the current device, then confirm secure storage is empty;
5. replay or revoke a credential and confirm the client clears local state and fails closed.

Android backup exclusion is configured by the Expo SecureStore config plugin. Shared
development logs must never print request bodies, authorization headers, or storage values.

## Scope boundary

S04-D06 adds the accessible foreground hold-to-talk experience and deterministic
client safety tests only. It does not add proximity, channel selection, user channels,
background transmission, hands-free/toggle behavior, recording, transcription,
provider deployment, or any cloud resource. Hardening, operations/evidence, and final
review remain assigned to S04-D07–D09. Real-device audio route, interruption,
Bluetooth, network transition, battery, latency, screen-reader gesture, and LiveKit
Cloud outcomes remain pending approved physical/provider evidence.
