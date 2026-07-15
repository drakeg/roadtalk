# RoadTalk Threat Model

- Status: Approved baseline
- Issue: #12
- Requirements: S00-R09
- Acceptance: S00-T07
- Date: 2026-07-12

## Assets

- account/session/device credentials
- anonymous recovery keys and their server-side hashes
- callsigns and public profiles
- exact and derived location
- channel and block/mute state
- media grants and room identifiers
- live audio
- push tokens
- infrastructure credentials and Terraform state
- operational logs and backups

## Trust boundaries

Device, public network, control API, media provider, database/cache, cloud operations, CI/CD, and support/administration are separate boundaries. Authentication at one boundary never grants unrestricted access across another.

## Threat register

| ID | Threat | Prevention | Detection/response | Residual risk |
|---|---|---|---|---|
| T01 | Stolen/replayed session credential | Short access TTL, rotating refresh family, secure device storage, TLS, revocation | Reuse detection, session/device audit, revoke family | Compromised device remains difficult to distinguish. |
| T02 | Anonymous-account farming/spam | Device/IP throttles, progressive trust, callsign limits, behavioral controls | Rate/anomaly metrics, suspend device/account | Determined attackers can rotate networks/devices. |
| T03 | Callsign impersonation | Normalization, uniqueness, reserved names, moderation | Change audit and reports | Similar-looking Unicode requires confusable policy. |
| T04 | Spoofed location | Freshness, accuracy, sequence, plausibility, device signals where justified | Impossible-travel and anomaly events | Consumer devices cannot provide cryptographic GPS proof. |
| T05 | Precise-location disclosure | Never return coordinates, minimize logs/retention, authorization | Payload/log scanning, privacy incident process | Nearby membership can imply approximate proximity. |
| T06 | Unauthorized listening | Server eligibility, short scoped LiveKit tokens, subscribe grants | Join/grant audit, revoke/remove participant | Active token valid until short expiry under provider limitation. |
| T07 | Unauthorized transmission | Publish-scoped grants, one publisher/device, rate limits | Concurrent grant alarms, revoke/remove | Token theft within TTL. |
| T08 | Media-token replay | Short TTL, unique participant/room, TLS, no token logging | Duplicate participant/grant telemetry | Provider revocation semantics require fail-safe TTL. |
| T09 | Audio interception | WebRTC encryption, TLS signaling, secret separation | Connection-quality/security telemetry | Endpoint compromise can capture audio. |
| T10 | Harassment/mute bypass | Server-enforced block/mute before grants | Reports, audit, enforcement review | New anonymous accounts may evade social controls. |
| T11 | API/WebSocket denial of service | Rate/concurrency limits, timeouts, bounded payloads, autoscaling path | Saturation/error alarms, incident runbook | Volumetric attack may require WAF/provider controls. |
| T12 | Media/TURN cost exhaustion | Grant limits, concurrency caps, usage budgets, no public credentials | Spend/usage anomaly alarms, kill switch | Legitimate spikes resemble abuse. |
| T13 | Injection/malformed input | Typed schemas, parameterized ORM/SQL, length/format limits | Error telemetry, dependency scanning | Logic flaws remain possible. |
| T14 | Sensitive log leakage | Central redaction, allowlisted fields, no body logging for sensitive routes | Automated scans and reviews | Developer-added logs can bypass policy. |
| T15 | Database/cache exposure | Private network, SG references, encryption, least privilege | AWS configuration monitoring, audit logs | Credential misuse within allowed path. |
| T16 | Mobile local-storage leakage | Platform secure storage, no exact-location history/audio, backup exclusions | MASVS storage testing | Rooted/jailbroken devices weaken guarantees. |
| T17 | Malicious dependency/build | Lockfiles, SBOM, signatures/checksums, scanning, protected CI | Dependabot/scanners and release provenance | Upstream compromise cannot be eliminated. |
| T18 | CI/cloud credential theft | OIDC, short-lived roles, MFA, secret manager, least privilege | CloudTrail and alerting | Privileged operator compromise. |
| T19 | Terraform state exposure | Encrypted/versioned private S3, locked access, no plaintext secrets | CloudTrail, access review | State may contain provider/resource metadata. |
| T20 | Backup/data-remanence failure | Retention/lifecycle, encrypted backups, deletion process | Restore/deletion audits | Backups delay full deletion within disclosed window. |
| T21 | Administrator abuse | Separate admin auth, least privilege, audit, no routine exact-location access | Immutable/security logs and periodic review | Authorized insiders retain bounded power. |
| T22 | Unsafe use while driving | Voice-first UI, restricted interaction, no safety guarantees | Product telemetry/reports without surveillance | Users may interact contrary to warnings/law. |
| T23 | Recovery-key theft, enumeration, or replay | 256-bit secret, slow salted/peppered hash, constant-shape errors, multidimensional limits, one-time display, explicit SecureStore opt-in, rotation and session revocation | Stable problem codes and privacy-safe route-template logs; contain by rotating key, revoking device/session, or rotating pepper after impact review | A stolen valid key can take over an anonymous account before the owner rotates it. A lost key cannot be bypassed safely. |

## Mandatory security controls before field test

- threat-mapped automated tests
- TLS everywhere across public paths
- secure token storage and refresh rotation
- no credentials in source, images, logs, or Terraform variables
- server-side authorization for every grant
- rate/concurrency/spend limits and kill switches
- dependency and container scanning
- privacy-filtered structured logging
- encrypted storage/backups
- tested account/device/session revocation
- tested recovery rotation, replay rejection, and non-enumerating failures
- tested backup restoration
- incident runbook and operational contact
- OWASP MASVS baseline checklist for storage, crypto, auth, network, platform, code, resilience, and privacy

## Incident priorities

- **P0:** confirmed live audio interception, broad credential compromise, or active exact-location disclosure
- **P1:** unauthorized listening/transmission, production secret exposure, material abuse/cost attack
- **P2:** bounded account compromise, repeatable control failure without broad exposure
- **P3:** low-impact hardening or telemetry defect

P0/P1 triggers containment, credential/token revocation, preservation of privacy-filtered evidence, product-owner notification, and a documented recovery decision.

## Acceptance result

Every named Sprint 0 threat has prevention, detection/response, and residual-risk treatment. Risks requiring implementation evidence are mapped to field-test gates rather than marked eliminated.

## References

- [OWASP MASVS](https://mas.owasp.org/MASVS/)
- [MASVS storage controls](https://mas.owasp.org/MASVS/05-MASVS-STORAGE/)
- [MASVS authentication](https://mas.owasp.org/MASVS/07-MASVS-AUTH/)
- [LiveKit tokens and grants](https://docs.livekit.io/frontends/reference/tokens-grants/)
