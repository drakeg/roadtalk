# Sprint 11 D07 mobile convoy evidence

The mobile app now exposes convoy lifecycle and awareness through the D06 authenticated server API only.

## Fail-closed behavior
- The client does not inspect device location to derive convoy state.
- Signed-out, request failure, offline, permission-denied, stale, revoked, or mismatched awareness clears the displayed convoy and member state rather than retaining cached presence.
- Awareness is accepted only when its convoy ID matches the current server membership.
- Member presentation is limited to callsign, role and fixed current availability returned by the server.
- Leave and leader disband require destructive confirmation.
- Convoy membership remains context only and cannot broaden communication authorization.

## Privacy and cost
No coordinates, routes, movement history, background location, background audio, new native permission, external provider, cloud resource, analytics, or recurring-spend dependency is added. Incremental recurring implementation cost remains $0.

## Automated evidence
Mobile API tests cover authenticated endpoint use and bounded mutation payloads. Screen tests cover server-returned awareness, stale/offline state clearing, and destructive confirmation. Home navigation coverage is synchronized.
