# RoadTalk Non-Functional Requirements

- Status: Approved MVP targets
- Issue: #13
- Requirements: S00-R11
- Acceptance: S00-T09
- Date: 2026-07-12

Targets apply to controlled MVP field testing unless explicitly marked production. They are hypotheses to validate, not marketing promises.

| ID | Area | Target | Test method |
|---|---|---|---|
| NFR-01 | PTT latency | Press-to-audible p50 ≤ 500 ms, p95 ≤ 900 ms on stable broadband/cellular; record degraded-network results separately. | Timestamp instrumented sender press/media publish and receiver first decoded audio across physical devices. |
| NFR-02 | Grant latency | PTT grant API p95 ≤ 250 ms within the deployment Region excluding client network. | Load test authenticated eligible and denied requests. |
| NFR-03 | API latency | REST p95 ≤ 300 ms for ordinary operations; proximity endpoint p95 ≤ 400 ms at field-test data scale. | Server-side histograms and load tests. |
| NFR-04 | Reconnect | Control reconnect p95 ≤ 5 s and media reconnect p95 ≤ 8 s after recoverable Wi-Fi/cellular transition. | Physical-device transition matrix. |
| NFR-05 | Availability | Field test best effort with documented single-instance limitation; production target 99.5% monthly before public claim. | Synthetic health checks and monthly calculation excluding approved maintenance only when disclosed. |
| NFR-06 | Recovery | Field-test RPO ≤ 24 h, RTO ≤ 4 h; restore tested before external field test. | Delete/restore rehearsal with recorded times and checks. |
| NFR-07 | Capacity | Initial controlled test: 100 registered, 25 concurrently connected, 10 simultaneous publishers across rooms/channels without missing latency/error targets. | Staged API/WebSocket/media load and soak tests. |
| NFR-08 | Proximity correctness | 100% pass on boundary, stale, inaccurate, consent, block/mute, and channel test matrix; no unauthorized grant. | Deterministic PostGIS fixtures and authorization tests. |
| NFR-09 | Battery | One hour receive-ready field test adds ≤ 8 percentage points battery drain on representative supported devices; active PTT scenario measured separately. | Fixed-brightness physical-device trials with OS battery reports. |
| NFR-10 | Mobile data | Receive-ready control traffic ≤ 10 MB/hour excluding audio; audio data measured and reported per active minute. | Device/network capture over scripted scenario. |
| NFR-11 | Privacy | Zero exact coordinates, refresh credentials, media tokens, audio, or push tokens in routine logs/errors/analytics. | Automated log corpus scan plus manual review. |
| NFR-12 | Security | No open critical/high findings in scoped dependency, container, IaC, API, and MASVS baseline checks before field test. | CI scanners and documented manual checklist. |
| NFR-13 | Accessibility | Core PTT flow supports screen-reader labels, dynamic text, contrast, non-color state cues, and 44×44 pt / 48×48 dp target guidance. | VoiceOver/TalkBack and manual accessibility checklist. |
| NFR-14 | Platform | Sprint 1 records exact minimum iOS/Android versions based on supported Expo/LiveKit release; test current and previous major OS where practical. | Dependency support review and device matrix. |
| NFR-15 | Observability | Every server request has correlation ID; actionable alerts for availability, error rate, saturation, database, grant failures, and spend. | Fault injection and alert-delivery test. |
| NFR-16 | Data lifecycle | Presence/location expiry within policy tolerance; deletion begins immediately and completes active systems within 24 h, backups within disclosed window. | Time-controlled lifecycle/deletion tests. |
| NFR-17 | Deployability | Reproducible clean setup; field-test deployment/rollback documented; no manual hidden state. | Runbook executed by a clean environment/operator. |
| NFR-18 | Maintainability | ≥80% coverage for backend domain logic as a guardrail, plus 100% explicit tests for authorization/proximity decision branches. | CI coverage and decision-table inspection. |

## Network test profiles

- stable Wi-Fi
- stable LTE/5G
- Wi-Fi to cellular and cellular to Wi-Fi
- 100 ms and 250 ms added RTT
- 1%, 3%, and 5% packet loss
- restricted NAT/TURN relay
- brief loss of connectivity
- background/foreground and screen-lock transitions

## Exit rule

A failed security/privacy authorization target blocks field testing. Performance/battery targets may be revised only through documented evidence and product-owner approval; they may not be silently marked passed.

## Primary references

- [LiveKit deployment guidance](https://docs.livekit.io/transport/self-hosting/deployment/)
- [Expo Audio battery warning](https://docs.expo.dev/versions/latest/sdk/audio/)
- [Expo Location platform constraints](https://docs.expo.dev/versions/latest/sdk/location/)
- [OWASP MASVS](https://mas.owasp.org/MASVS/)
