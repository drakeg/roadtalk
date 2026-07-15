# Mobile

Sprint 2 owner: S02-D05, S02-D06, and S02-D08.

This directory contains the Expo/React Native/TypeScript development-build application.

## Current foundation

Sprint 1 and S02-D05 provide:

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
5. confirm no location, microphone, notification, or tracking permission is requested.

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

The authenticated shell exposes no location, audio, PTT, proximity, or channel feature.
Later domains remain unavailable until their approved sprints.
