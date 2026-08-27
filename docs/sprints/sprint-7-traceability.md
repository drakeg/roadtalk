# Sprint 7 Traceability — Route Awareness

## Status

S07-D09 review candidate. This record traces the approved Sprint 7 requirements,
acceptance tests, delivery issues, merged pull requests, automated evidence, and named
evidence exceptions. Product-owner acceptance is recorded only by merging the S07-D09
review pull request.

Sprint 7 remains a **local/GitHub-CI synthetic milestone**. No real routing provider,
road dataset, AWS resource, LiveKit Cloud resource, payment method, production/public
beta, or recurring spend was activated.

## Bidirectional requirement/test/delivery evidence

| Requirement | Acceptance | Delivery / PR | Primary evidence | Result / limitation |
|---|---|---|---|---|
| **S07-R01 — Explicit route mode** | **S07-T01** | S07-D02 #165 / PR #175 | route-mode API/service/database tests; migration `0012`; `check-route-mode-privacy.py` | Nearby remains default; authenticated/versioned exact Nearby/Same-road transitions only; over-posting and conflicts deny. |
| **S07-R02 — Provider boundary** | **S07-T02** | S07-D03 #166 / PR #177 | `test_route_context_provider.py`; `check-route-context-provider.py` | Typed minimized request/result, deterministic fake, bounded timeout and validation; config supports only disabled/fake. Real provider not implemented or called. |
| **S07-R03 — Context minimization** | **S07-T03** | S07-D04 #167 / PR #178 | migration `0013`; `route_context/models.py`; lifecycle/database tests; D08 hardening gate | One current minimized context row with keyed corridor digest/coarse direction/confidence/source version/policy/expiry; no trace, geometry, road name or provider payload retained. |
| **S07-R04 — Match integrity** | **S07-T04** | S07-D04 #167 / PR #178 | route-context lifecycle/provider/database tests | Context binds to accepted location version; stale, inaccurate, ambiguous, out-of-order, mismatched, low-confidence and provider-failed results cannot become valid context. |
| **S07-R05 — Composed authorization** | **S07-T05** | S07-D05 #168 / PR #180 | `test_ptt_proximity.py`; existing channel/session/grant tests; route-aware scale test | Sprint 5 PostGIS/channel/session/grant predicates run first; Same-road only removes already-authorized recipients. No prior denial becomes eligible. |
| **S07-R06 — Direction/corridor policy** | **S07-T06** | S07-D05 #168 / PR #180 | `test_ptt_proximity.py`; D08 100/25/10 matrix | Exact keyed corridor equality plus deterministic coarse adjacent-direction compatibility; wraparound supported; stationary/unknown deny Same-road. |
| **S07-R07 — Failure/reconciliation** | **S07-T07** | S07-D06 #169 / PR #181 | route-context operations/lifecycle tests; PTT reconciliation tests; logging/system metric tests; `route-awareness-operations.md` | Timeout/error/expiry/mode/pause/withdrawal/revocation/deletion paths fail closed and use bounded cleanup/reconciliation. No always-on retry worker added. |
| **S07-R08 — Client experience** | **S07-T08** | S07-D07 #170 / PR #182; hardening PR #183 | mobile `RouteModeScreen` tests; route-mode browser tests; `test_browser_hardening.py` | Mobile/browser expose generic Nearby/Same-road/matching/unavailable/error states without road/route/identity/location disclosure. Browser secure-context/mic/location behavior is automated evidence only, not broad physical-system proof. |
| **S07-R09 — Privacy/security/licensing** | **S07-T09** | S07-D08 #171 / PRs #183, #184 | `check-route-awareness-hardening.py`; route-mode/provider gates; dependency/privacy/security scans; `docs/evidence/sprint-7/README.md` | No prohibited route/provider/identity/eligibility leakage or external provider/data activation. ODbL attribution/share-alike obligations are recorded before any future OSM-derived dataset activation. |
| **S07-R10 — Reliability/performance** | **S07-T10** | S07-D08 #171 / PR #184 | `test_route_awareness_scale.py`; Sprint 7 hardening workflow; full regression CI | 100 accounts/25 receivers/10 publishers synthetic PostGIS/control-plane matrix passes. Named first-run p95: Nearby 40.71 ms; Same-road 24.03 ms; zero-recipient denial 18.97 ms; reconciliation 160.94 ms, each under 400 ms. Not live media/provider/device performance. |
| **S07-R11 — Cost controls** | **S07-T11** | S07-D01–D08; PR #184 evidence | `.env.example`; disabled Terraform validation; Compose validation; provider hard-disable gate; Sprint 7 evidence record | Current/incremental recurring cost remains **$0 AWS + $0 LiveKit Cloud + $0 routing provider/month**. No external route request, dataset download or new cloud resource. |
| **S07-R12 — Compatibility/scope** | **S07-T12** | S07-D01–D09; final review PR | all normal CI, dedicated Sprint 7 hardening CI, this traceability and final review | Sprints 1–6 regressions remain green and prohibited Sprint 8+/production scope remains excluded. Named live/provider/device/field exceptions remain open. |

## Acceptance-test index

- **S07-T01:** route-mode default/auth/version/conflict/over-posting evidence — PR #175.
- **S07-T02:** typed fake provider/minimized request/timeout/malformed/unknown-provider evidence — PR #177.
- **S07-T03:** minimized current-context schema/migration/replacement/deletion evidence — PR #178.
- **S07-T04:** source-location binding, ordering, freshness, confidence and concurrency evidence — PR #178.
- **S07-T05:** proximity/channel/session/grant/mode/route composition evidence — PR #180.
- **S07-T06:** keyed corridor and coarse direction/wraparound/unknown policy evidence — PR #180.
- **S07-T07:** provider/database/media failure and lifecycle reconciliation evidence — PR #181.
- **S07-T08:** mobile/browser generic mode and unavailable-state evidence — PRs #182 and #183.
- **S07-T09:** API/schema/config/dependency/log/evidence leakage plus licensing/activation gate — PR #184.
- **S07-T10:** full regression plus route-aware **100 accounts/25 receivers/10 publishers** synthetic matrix — PR #184.
- **S07-T11:** Compose/provider/dataset/network/dependency/disabled-IaC and $0 evidence — PR #184 plus normal CI.
- **S07-T12:** this bidirectional traceability, final review, risk/limitations record, and product-owner merge acceptance — S07-D09 / #172.

## Delivery index

- **S07-D01:** specification/readiness/tracker — planning PR #164, readiness approval PR #174, tracker #173.
- **S07-D02:** route mode contract/persistence — issue #165 / PR #175.
- **S07-D03:** route-context provider boundary — issue #166 / PR #177.
- **S07-D04:** current route-context lifecycle — issue #167 / PR #178.
- **S07-D05:** Same-road authorization composition — issue #168 / PR #180.
- **S07-D06:** failure reconciliation/operations — issue #169 / PR #181.
- **S07-D07:** mobile/browser Same-road experience — issue #170 / PR #182.
- **S07-D08:** browser release hardening plus security/privacy/licensing/performance evidence — issue #171 / PRs #183 and #184.
- **S07-D09:** traceability/review/product-owner acceptance — issue #172 / final review PR.

## Synthetic lifecycle demonstration

The accepted synthetic lifecycle is:

1. An authenticated account defaults to Nearby and may explicitly select Same road with
   optimistic versioning.
2. Existing Sprint 3 foreground consent/location validation accepts the current sample.
3. Same-road mode passes a minimized sample to the deterministic fake provider; no
   network request occurs.
4. A confident fake match replaces the account's one short-lived route-context row,
   bound to that exact location version.
5. Existing Sprint 5 proximity plus Sprint 6 channel/session/grant rules produce the
   candidate audience first.
6. Same-road then retains only fresh/confident contexts with the same keyed corridor
   digest and compatible coarse direction.
7. Mismatch, missing/expired context, stationary/unknown direction, provider failure or
   earlier authorization denial produces no Same-road recipient and reveals no reason.
8. Pause, consent withdrawal, logout, deletion, revocation, expiry or mode transition
   invalidates/removes context/media authority and bounded reconciliation removes stale
   provider delivery state.

The D08 matrix explicitly demonstrates both Nearby preservation and Same-road reduction:
25 receive grants remain eligible to Nearby publishers, 20 remain eligible to matching
Same-road publishers, five are denied by corridor/direction policy, and a mismatched
Same-road publisher reaches zero recipients.

## Named performance evidence

Authoritative Sprint 7 hardening run `33035376277` recorded on 2026-08-27:

- Nearby eligible lookup p95: **40.71 ms**;
- Same-road eligible lookup p95: **24.03 ms**;
- Same-road zero-recipient denial p95: **18.97 ms**;
- bounded publication/subscription reconciliation p95: **160.94 ms**;
- target: **400 ms p95**.

Final D08 validation also passed dedicated hardening run `33035637402` and normal CI
run `33035637450`, covering backend/database/migrations/full tests, mobile quality,
dependency/privacy/IaC gates, container build and image scan.

## Approved evidence exceptions / unperformed work

These are intentionally **not** acceptance claims and remain prerequisites for any
future field/production assertion:

- real-road matching quality, ambiguity, map completeness/freshness or provider latency;
- selection, licensing compliance and distribution of a real production road dataset;
- physical-device GPS accuracy, battery/data behavior, mobile OS permission behavior or
  background operation;
- cross-browser/physical-system microphone/speaker, Bluetooth, interruption and
  accessibility-gesture validation;
- live media latency/jitter/loss, NAT/TURN, cellular/Wi-Fi handoff or live subscription
  revocation;
- AWS deployment, billing, destroy, production/public beta or multi-worker capacity;
- emergency, safety, navigation, hands-free or driver-distraction claims.

Sprint 1 field blockers S01-E01 through S01-E03 remain relevant to physical field
validation and are not closed by synthetic Sprint 7 evidence.

## Reverse traceability rule

Every Sprint 7 implementation artifact must map back to S07-R01–R12 and the locked
D01–D09 sequence. Any future feature that cannot be traced to this Sprint 7 record is
not retroactively authorized by Sprint 7 and requires a later approved Sprint/decision.
