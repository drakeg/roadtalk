# ADR-0001: Mobile application platform

- Status: Accepted
- Date: 2026-07-12
- Deciders: Product owner and RoadTalk architecture review
- Sprint: 0
- Requirements: S00-R02, S00-R08, S00-R10, S00-R11

## Context

RoadTalk requires one mobile experience for iOS and Android with microphone, realtime audio, location, background behavior, notifications, secure storage, maps, and network-transition handling. A small initial team benefits from shared UI and business logic, but the application cannot depend on a sandbox that prevents necessary native capabilities.

## Decision

Use React Native with Expo development builds and TypeScript for the MVP mobile application.

Use Expo's development-build and configuration-plugin workflow rather than treating Expo Go as the production runtime. Native iOS and Android projects may be generated and extended when a required capability cannot be supplied safely through an existing supported module.

Adopt the React Native New Architecture unless a required, validated dependency proves incompatible.

## Rationale

- one primary TypeScript codebase reduces duplicated iOS/Android feature work
- React Native retains an escape path through native modules
- Expo provides supported location, audio, task, permission, build, and update tooling
- LiveKit documents an Expo integration using its React Native WebRTC SDK
- build-time permission descriptions and native configuration can be reviewed early
- the approach supports incremental native specialization without starting with two independent applications

## Constraints

- background location stops when a user terminates the application on iOS; the product must not promise otherwise
- background recording can materially affect battery life and is not enabled by default
- microphone and location permission text is part of the product/privacy design
- Expo Go is insufficient as the sole development environment for custom native WebRTC behavior
- native modules and configuration must be tested on physical iOS and Android devices
- push-to-talk must remain usable with screen-lock, audio-route, Bluetooth, interruption, and network-transition behavior explicitly tested before production

## Alternatives considered

### Separate Swift and Kotlin applications

Best native control and platform fidelity, but duplicates product work and slows MVP validation for a small team. Retain as a future option if measured reliability or platform restrictions make the shared approach unacceptable.

### Flutter

Provides one codebase and strong UI tooling, but RoadTalk's proposed realtime stack has a documented React Native/Expo path and the team's backend/mobile integration benefits from TypeScript ecosystem alignment.

### Progressive web application

Rejected for the MVP because background location, audio routing, microphone lifecycle, notifications, screen-lock behavior, and store-grade mobile integration are central requirements.

## Consequences

### Positive

- shared feature delivery across iOS and Android
- direct path to documented LiveKit React Native support
- native extension remains possible
- TypeScript can share schemas and client types

### Negative

- dependency compatibility must be monitored
- advanced audio behavior may require native work
- platform-specific behavior and store policies still require separate testing
- development builds and physical devices are mandatory

## Validation

- build and install development builds on current supported iOS and Android targets
- validate microphone, speaker/Bluetooth routing, background/lock behavior, and interruption handling
- validate foreground and approved background location behavior
- validate LiveKit publish/subscribe on physical devices across Wi-Fi and cellular transitions
- measure battery and data usage against S00-D11 targets

## Sources

- [Expo development builds](https://docs.expo.dev/develop/development-builds/introduction/)
- [Expo Location](https://docs.expo.dev/versions/latest/sdk/location/)
- [Expo Audio](https://docs.expo.dev/versions/latest/sdk/audio/)
- [Expo Permissions](https://docs.expo.dev/guides/permissions/)
- [LiveKit Expo quickstart](https://docs.livekit.io/transport/sdk-platforms/expo/)
- [React Native native modules](https://reactnative.dev/docs/turbo-native-modules-introduction)
