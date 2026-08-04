# Sprint 4 physical-device media test record

- Status: Not run
- Date/time (UTC):
- Operator and observer:
- Reviewer:
- Commit and immutable build identifiers:
- Approved issue/change record:
- Device classes and OS versions (no unique device IDs):
- Network classes (no addresses or SSIDs):
- Approved start/end time:
- Maximum projected incremental cost:

## Preconditions

- [ ] Applicable Sprint 1 exceptions are closed
- [ ] LiveKit Build activation and any AWS use are separately approved
- [ ] Current provider/AWS pricing and month-to-date aggregate usage were checked
- [ ] Entire script remains below 3,000 participant-minutes, 10 GB, 25 connections, and $10
- [ ] Synthetic accounts and speech content only
- [ ] No recording, screenshot containing values, packet capture, transcript, or raw log
- [ ] Provider credentials use a masked server-only secret path
- [ ] Stop/revoke/destroy operator remains available through verification

## Results

Record pass/fail, aggregate timing/usage, and observer confirmation only. Do not record
token, secret, callsign, account/device/session, room/participant, network, or audio values.

| Check | Expected | Aggregate/observed result | Pass/fail | Safe evidence reference |
|---|---|---|---|---|
| Purpose before permission | Explanation precedes OS prompt; denial remains usable |  |  |  |
| Receive-ready | Remote synthetic audio is heard; local capture remains off |  |  |  |
| Hold to talk | Capture begins only after authorization and only while held |  |  |  |
| Release/maximum | Capture stops before cleanup on release and at 30 seconds |  |  |  |
| Incoming/busy | Incoming speech and busy state remain understandable and fail closed |  |  |  |
| Background/exit/logout | Every lifecycle exit stops capture and disconnects |  |  |  |
| Permission revoked | Revocation stops media and provides safe recovery guidance |  |  |  |
| Wi-Fi/cellular transition | Reconnect never publishes without new authority |  |  |  |
| Restrictive NAT/TURN | Bounded connection result; no unauthorized fallback |  |  |  |
| Audio route/interruption | Speaker/receiver/Bluetooth and interruption result recorded by class only |  |  |  |
| Accessibility | Screen-reader hold/release gesture, labels, large text, and non-color cues work |  |  |  |
| Performance | Aggregate join/publish/stop latency, jitter/loss, battery, and data use |  |  |  |

## Aggregate usage and cost

- Participant-minutes before / after:
- Downstream GB before / after:
- Peak concurrent participants:
- AWS month-to-date before / after:
- Estimated / actual incremental cost:
- Any review point reached:
- Any hard stop reached and containment time:

## Cleanup verification

- [ ] All devices disconnected and synthetic grants revoked
- [ ] Provider keys revoked and disposable project deleted or left with no valid key/session
- [ ] AWS stack destroyed if used; disabled and post-destroy plans report zero resources
- [ ] Independent cloud inventory found no unapproved retained item
- [ ] No sensitive value or audio entered retained evidence
- [ ] Delayed billing/usage recheck assigned

## Decision

- [ ] Passed
- [ ] Failed
- [ ] Blocked

Limitations, follow-ups, owners, and due dates:

Reviewer approval:
