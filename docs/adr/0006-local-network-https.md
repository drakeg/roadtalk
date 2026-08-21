# ADR 0006: Opt-in local-network HTTPS testing

- Status: Proposed; accepted when the implementing pull request is merged
- Date: 2026-08-20
- Scope: Post-Sprint-6 local alpha readiness only

## Context

RoadTalk's default Docker Compose environment binds the browser application to
loopback. That is the safest default, but it prevents testing from another computer,
phone, or tablet on the developer's trusted home network. Merely binding HTTP to a
private address is insufficient: browser microphone and geolocation APIs require a
secure context when the origin is not localhost.

This change must not create cloud infrastructure, activate LiveKit Cloud, expose the
application to the public internet, or weaken the normal loopback default.

## Decision

Keep the default Compose stack loopback-only. Add a separate Compose override and
Make targets that require the Docker host's explicit private IP address.

The override:

- runs the pinned official Caddy image as an HTTPS gateway;
- uses Caddy's local certificate authority for a device-trusted development
  certificate;
- proxies the RoadTalk web/API origin and LiveKit WebSocket signaling through one
  HTTPS origin;
- tells local LiveKit to advertise the Docker host's private IP for WebRTC;
- publishes only the already-required local WebRTC transport ports;
- requires manual CA installation and trust on each test device.

The workflow is restricted to a trusted private network. Router port forwarding,
public DNS, public exposure, and shared or production credentials remain prohibited.

## Consequences

- Browser microphone and location permissions work from trusted LAN devices after the
  local CA is installed.
- Testers must explicitly start and stop LAN mode and may need host-firewall rules for
  TCP 8443/7881 and UDP 7882.
- Compromise of the local Caddy CA would allow certificate issuance trusted by devices
  where that CA was installed. The CA file therefore remains ignored, should be
  transferred securely, and should be removed from devices after testing if no longer
  needed.
- This is local alpha tooling, not a production deployment topology and not Sprint 7
  route-awareness implementation.
