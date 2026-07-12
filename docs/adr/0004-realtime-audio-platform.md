# ADR-0004: Realtime audio platform

- Status: Accepted
- Date: 2026-07-12
- Deciders: Product owner and RoadTalk architecture review
- Sprint: 0
- Requirements: S00-R01, S00-R02, S00-R05, S00-R09, S00-R10, S00-R11

## Context

Push-to-talk requires low-latency encrypted audio, mobile SDKs, NAT traversal, reconnection, publish/subscribe authorization, and network-quality telemetry. Implementing a WebRTC SFU and TURN stack from first principles would dominate the MVP and create avoidable security and reliability risk.

RoadTalk also needs application-specific rules: only eligible nearby/channel participants may publish or subscribe, and those decisions must remain under RoadTalk control.

## Decision

Use LiveKit as the WebRTC media platform for the MVP.

The RoadTalk control API:

- determines eligibility
- creates short-lived, least-privilege room grants
- controls publish and subscribe permissions
- never exposes LiveKit API secrets to clients
- never proxies media packets
- expires grants and rooms aggressively
- records technical metadata only as permitted by the privacy model

Use audio-only rooms/tracks. Disable recording, egress, transcription, and durable media storage for Sprints 1–5.

Use LiveKit Cloud initially for field testing and the managed production baseline. Self-hosting requires a superseding ADR supported by measured cost, control, compliance, and operational evidence.

## Rationale

- LiveKit provides documented React Native and Expo integrations
- WebRTC supplies realtime encrypted media and NAT traversal primitives
- a specialized SFU avoids building and securing a media server
- token grants allow the RoadTalk API to retain application authorization
- media scaling remains separate from the control API

## Constraints

- self-hosted deployment requires UDP/TCP/TURN ports and deliberate TLS/network design
- clustered self-hosting requires Redis and layer-4 load balancing
- self-hosted token revocation has limitations; use short token TTLs and do not automatically reissue after removal
- no assumption that ALB WebSocket support makes it suitable for all WebRTC media paths
- cellular transitions, packet loss, NAT types, Bluetooth routes, interruptions, and background behavior require physical-device testing
- any future recording, transcription, translation, or AI processing requires a new privacy/security decision

## Alternatives considered

### Build directly on open-source WebRTC libraries

Maximum control, but requires RoadTalk to build and operate signaling, SFU, TURN, congestion, reconnection, SDK integration, and security behavior. Rejected for MVP scope.

### AWS communication SDK

Potential AWS integration benefits, but the architecture must still implement RoadTalk-specific push-to-talk and proximity semantics. Retain as a comparison candidate during the detailed AWS/media cost review.

### Traditional audio upload and playback

Simpler transport but cannot satisfy low-latency conversational push-to-talk expectations.

### SIP/telephony system

Designed for telephone interoperability rather than nearby app-native communication and adds unnecessary infrastructure for the MVP.

## Consequences

### Positive

- materially reduces media implementation scope
- cross-platform mobile SDK path
- separate scaling and telemetry for media
- retains RoadTalk authorization control

### Negative

- introduces a critical third-party/open-source platform dependency
- cloud use creates metered vendor cost
- self-hosting creates TURN, networking, upgrades, and capacity obligations
- field conditions may expose SDK/platform limitations

## Validation

- compare LiveKit Cloud and self-hosted costs and operational risks
- prototype audio-only publish/subscribe on physical iOS and Android devices in Sprint 1 or an explicitly approved technical spike
- measure press-to-audible latency, packet loss, reconnect time, battery, and mobile-data usage
- test Wi-Fi/cellular transitions and restrictive NAT environments
- verify grant scope, expiry, removal, and failure-closed behavior
- verify that audio and exact coordinates are absent from logs and durable storage

## Sources

- [LiveKit Expo quickstart](https://docs.livekit.io/transport/sdk-platforms/expo/)
- [LiveKit React Native quickstart](https://docs.livekit.io/transport/sdk-platforms/react-native/)
- [LiveKit self-hosted deployment](https://docs.livekit.io/transport/self-hosting/deployment/)
- [LiveKit VM deployment](https://docs.livekit.io/transport/self-hosting/vm/)
- [LiveKit tokens and grants](https://docs.livekit.io/frontends/reference/tokens-grants/)
- [LiveKit quotas and limits](https://docs.livekit.io/deploy/admin/quotas-and-limits/)
