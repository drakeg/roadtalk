# Mobile

Sprint 1 owner: S01-D02 and S01-D06.

This directory contains the Expo/React Native/TypeScript development-build application.

## Current foundation

S01-D02 and S01-D06 provide:

- Expo SDK 57 with React Native 0.86 and the New Architecture
- iOS and Android development-client configuration
- typed public API endpoint configuration
- accessible native-stack navigation shell
- application-level error boundary with retry behavior
- Jest and React Native Testing Library smoke tests
- strict TypeScript and Expo Doctor validation
- no profile, location, audio, PTT, proximity, or channel behavior
- anonymous device registration and session bootstrap
- refresh credentials stored only through Expo SecureStore
- access credentials held only in process memory
- refresh rotation, logout, device revocation, and fail-closed recovery

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

Before S01-D02 is accepted:

1. install a development build on one supported iOS target and one supported Android target;
2. confirm the RoadTalk foundation screen launches;
3. confirm the diagnostics screen shows the intended API URL;
4. verify text scaling, screen-reader labels, button target size, light/dark system behavior, and error fallback;
5. confirm no profile, location, microphone, notification, or tracking permission is requested.

## Credential-storage verification

The client intentionally has no AsyncStorage dependency. Before accepting S01-D06:

1. inspect iOS Keychain and Android Keystore-backed SecureStore behavior on development builds;
2. verify raw access and refresh credentials do not appear in logs, screenshots, URLs,
   errors, analytics, ordinary files/preferences, or unencrypted backups;
3. rotate refresh credentials and confirm the old value is replaced;
4. log out and revoke the current device, then confirm secure storage is empty;
5. replay or revoke a credential and confirm the client clears local state and fails closed.

Android backup exclusion is configured by the Expo SecureStore config plugin. Shared
development logs must never print request bodies, authorization headers, or storage values.

## Scope boundary

The authenticated shell exposes no profile, location, audio, PTT, proximity, or channel
feature. Later domains remain unavailable until their approved sprints.
