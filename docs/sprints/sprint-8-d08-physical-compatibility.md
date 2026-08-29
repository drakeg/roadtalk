# Sprint 8 D08 — Physical microphone and location compatibility evidence

Status: **active evidence record**

Issue: #192  
Requirements: S08-R10 / S08-T10

## Purpose

This record captures only physical or simulator behavior that has actually been observed. It intentionally distinguishes **observed**, **failed**, **not performed**, and **not available** combinations. It does not infer support from automated tests alone.

D08 remains foreground-only. Nothing in this evidence authorizes background microphone/location, navigation, safety claims, public/cloud deployment, a hosted map provider, LiveKit Cloud, or paid test services.

## Evidence rules

- `PASS` means the named behavior was physically observed on the named system.
- `FAIL` means a reproducible product defect was physically observed.
- `PARTIAL` means only part of the row was physically observed.
- `NOT PERFORMED` means no claim is made.
- Browser/OS/version values are recorded only when known from the test observation.
- A permission prompt succeeding does not imply media transport, speaker receive, or location upload succeeded; each is recorded separately.

## Representative matrix

| ID | System | Origin / access mode | Microphone acquire | Mic denial + recovery | Foreground location acquire | Location denial + recovery | Receive / speaker | Result / evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PHY-01 | Physical MacBook, macOS; exact browser/version not recorded | RoadTalk browser session; exact localhost-vs-HTTPS-LAN mode not recorded | **PASS observed** | NOT PERFORMED | **PASS observed** | NOT PERFORMED | NOT PERFORMED | User physically observed RoadTalk showing microphone and location enabled after pressing **Start RoadTalk**. The subsequent failure was browser-session/account recovery, not permission acquisition. That defect was addressed by #201/#202 and then superseded for normal returning users by persistent registered-account login in #207. |
| PHY-02 | Same physical MacBook | `http://127.0.0.1` | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | Explicit exception: localhost behavior has not yet been separately recorded for D08. |
| PHY-03 | Same physical MacBook | RoadTalk HTTPS LAN gateway | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | Explicit exception: HTTPS-LAN behavior has not yet been separately recorded for D08. |
| PHY-04 | Physical iPhone / iOS browser | RoadTalk HTTPS LAN gateway | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | Hardware is potentially available, but no D08 result is claimed until the browser test is explicitly executed and recorded. |
| PHY-05 | Physical iPhone / native mobile app | Foreground app session | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | Native physical-device evidence remains pending. Automated mobile lifecycle tests are regression evidence, not a substitute for this row. |
| PHY-06 | iOS simulator | Simulator | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | Simulator evidence may supplement but cannot replace physical microphone/location evidence. |
| PHY-07 | Android physical device | Foreground app/browser | NOT AVAILABLE / NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | NOT PERFORMED | No Android hardware evidence is currently claimed. |

## Confirmed physical finding: MacBook permission acquisition

During browser testing on a physical MacBook, pressing **Start RoadTalk** resulted in both microphone and location being reported as enabled. The flow then failed with a browser-session error. This separates the compatibility result into two facts:

1. browser microphone acquisition succeeded on that physical system;
2. foreground geolocation acquisition succeeded on that physical system;
3. the post-permission authentication/session path failed independently.

The session/account defect was reproducible and led to #201/#202. Testing then exposed the larger product-model problem that returning users should authenticate a persistent account and retain their call sign. That was corrected by #207. Therefore the original failure is **not** evidence of a microphone or geolocation incompatibility.

## Current product behavior relevant to D08

The browser hardening layer must continue to:

- reject insecure remote origins where browser microphone/geolocation APIs are unavailable;
- support localhost (`127.0.0.1`) as a browser secure-context exception when the browser permits it;
- use the RoadTalk HTTPS LAN gateway for another physical device on the LAN;
- request microphone only in response to foreground user action;
- request geolocation only in the foreground;
- provide explicit blocked/unavailable diagnostics;
- stop temporary microphone preflight tracks immediately;
- avoid background audio/location collection;
- fail closed rather than claiming successful proximity/map behavior when location is unavailable.

## Manual execution procedure

For each physical row, record the browser/app version and date, then execute only the applicable steps:

1. Open RoadTalk using the named origin mode.
2. Sign in to the persistent RoadTalk account; verify the existing profile/call sign is restored.
3. Press **Start RoadTalk**.
4. Record whether the microphone prompt appears, whether Allow succeeds, and whether RoadTalk reports `Granted`.
5. When safe to do so, deny microphone permission, retry, and record whether the UI explains how to recover. Re-enable permission and verify recovery.
6. Record whether foreground geolocation prompts/acquires and whether RoadTalk reports `Granted`.
7. When safe to do so, deny location permission, retry, record the diagnostic, then re-enable and verify recovery.
8. If a second RoadTalk endpoint is physically available, verify speaker/receive behavior without asserting proximity accuracy or safety suitability.
9. Disconnect and verify no continuing background microphone/location activity is expected or claimed by RoadTalk.
10. Add the exact observation to the matrix; do not replace `NOT PERFORMED` with assumptions.

## Automated evidence that supports, but does not replace, physical testing

CI covers browser secure-context diagnostics, permission preflight behavior, session/account regression, mobile foreground lifecycle behavior, privacy contracts, build/container checks, and the existing security gates. These checks reduce regressions but are not counted as physical-system PASS rows.

## Known exceptions / release evidence gaps

The following remain explicit D08 evidence gaps until physically exercised:

- exact MacBook browser/version for PHY-01;
- separate localhost and HTTPS-LAN MacBook runs;
- physical browser microphone denial/recovery;
- physical browser geolocation denial/recovery;
- physical receive/speaker path;
- physical iPhone browser test;
- physical native iPhone app microphone/location test;
- Android physical-device evidence;
- any additional desktop OS/browser combination.

These gaps must not be silently converted into support claims. D08 can document unavailable hardware as an exception, but any release/readiness decision must carry those exceptions forward.

## Cost and activation boundary

All D08 evidence is limited to already-available local hardware, local Docker/LAN access, simulators, and GitHub CI. Incremental recurring cost remains **$0**. No AWS activation, hosted map/tile/geocoding provider, LiveKit Cloud activation, paid browser/device testing service, payment-info free tier, or public field test is authorized by this deliverable.
