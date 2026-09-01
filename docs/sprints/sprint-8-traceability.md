# Sprint 8 Traceability — Map Experience

## Status

S08-D10 review candidate. Product-owner acceptance is recorded only by merge of the
S08-D10 review pull request. Sprint 8 remains a **local/GitHub-CI milestone with limited
physical compatibility evidence**. No production/public map provider, AWS resource,
LiveKit Cloud resource, payment method, paid/free-tier provider account, public beta,
background location/audio, navigation feature, or recurring spend was activated.

## Bidirectional requirement/test/delivery evidence

| Requirement | Acceptance | Delivery / PR | Primary evidence | Result / limitation |
|---|---|---|---|---|
| **S08-R01 — Own-location map** | **S08-T01** | D05 #189 / PR #200; D06 #190 / PR #209; D07 #191 / PR #212 | browser/mobile map tests; `LocationLifecycleController` tests | Own accepted foreground location may render locally with active/stale/unavailable semantics; no background location permission. |
| **S08-R02 — Privacy-preserving presence contract** | **S08-T02** | D02 #186 / PR #197; D04 #188 / PR #199 | presence policy/schema tests; API over-posting/privacy tests | Other-user output is limited to coarse cells, density bucket, policy/freshness/expiry metadata; forbidden exact/identity/motion/route/history fields are rejected. |
| **S08-R03 — Sparse-population protection** | **S08-T03** | D02 #186 / PR #197 | deterministic sparse/duplicate/conflict privacy tests; Sprint 8 hardening gate | Fixed 2 km cells, minimum 3 distinct accounts, max 32 cells, `few`/`several`/`many`; one/two-account cells suppressed. |
| **S08-R04 — Authorization separation** | **S08-T04** | D04 #188 / PR #199 | lifecycle/authorization composition tests; existing Sprint 5–7 regression gates | Presence is read-only awareness. It cannot create or broaden receiver/publisher/channel/session/grant/Same-road eligibility. |
| **S08-R05 — Current-only lifecycle** | **S08-T05** | D04 #188 / PR #199 | disposable-DB lifecycle tests; session/consent/staleness tests | Presence derives from current location only; stale/revoked/inactive/withdrawn state fails closed; no presence-history table. |
| **S08-R06 — Map provider boundary** | **S08-T06** | D03 #187 / PR #198; D09 #193 / PR #216 | fake-provider tests; `check-map-presence-hardening.py` | Deterministic disabled/fake provider only; no URL/key/token/account/network/dataset production provider. |
| **S08-R07 — Browser experience** | **S08-T07** | D05 #189 / PR #200; D07 #191 / PR #212; account corrections PRs #201/#202/#207 | browser map/navigation/diagnostic/accessibility tests | Responsive browser awareness surface, secure-context/location diagnostics, privacy-safe degraded states, persistent registered-account path. |
| **S08-R08 — Mobile experience** | **S08-T08** | D06 #190 / PR #209; CI repairs #210/#211; D07 #191 / PR #212 | mobile Home/Map/Presence/lifecycle/accessibility tests | Foreground-only own-location awareness and coarse presence; exact other-user detail remains unavailable. |
| **S08-R09 — Accessible equivalent** | **S08-T09** | D07 #191 / PR #212 | browser/mobile accessibility regression tests | Text-equivalent awareness, labels/live status/focus semantics, degraded states hide stale coarse presence rather than implying precision. |
| **S08-R10 — Compatibility evidence** | **S08-T10** | D08 #192 / PR #215 | `sprint-8-d08-physical-compatibility.md` | Physical MacBook microphone and foreground-location acquisition observed. Exact browser/version, localhost-vs-HTTPS mode, denial/recovery, speaker receive, iPhone native/browser, and Android remain explicit unperformed/unavailable exceptions. |
| **S08-R11 — Hardening and performance** | **S08-T11** | D09 #193 / PR #216 | Sprint 8 hardening run #6; CI #401; Sprint 7 hardening #73; `test_presence_scale.py` | 100 registered accounts / 25 viewers / 10 publishers; lookup p95 3.44 ms, refresh p95 2.30 ms, both under locked 400 ms target. Synthetic CI/PostGIS only. |
| **S08-R12 — Evidence and review** | **S08-T12** | D10 #194 / final review PR | this traceability, `sprint-8-review.md`, review CI gate | Complete only upon product-owner merge of the D10 review PR; named physical/provider/cloud/field exceptions remain carried forward. |

## Acceptance-test index

- **S08-T01:** foreground own-location active/denied/stale/unavailable behavior — PRs #200, #209, #212.
- **S08-T02:** selector rejection and forbidden other-user field exclusion — PRs #197, #199, #216.
- **S08-T03:** sparse suppression/coarsening and duplicate/conflict handling — PR #197 plus D09 hardening.
- **S08-T04:** presence cannot broaden existing authorization — PR #199 plus Sprint 5–7 regression gates.
- **S08-T05:** expiry/consent/session/revocation/current-only lifecycle — PR #199.
- **S08-T06:** deterministic fake/disabled provider and real-provider/network disablement — PRs #198, #216.
- **S08-T07:** browser navigation/diagnostics/degraded/privacy-safe rendering — PRs #200, #212.
- **S08-T08:** mobile navigation/foreground lifecycle/degraded/privacy-safe rendering — PR #209, repaired tests #210/#211, accessibility PR #212.
- **S08-T09:** semantic controls/live status/text-equivalent awareness — PR #212.
- **S08-T10:** named physical compatibility matrix with explicit exceptions — PR #215.
- **S08-T11:** privacy/schema/log/provider/cost gates and 100/25/10 scale matrix — PR #216; Sprint 8 hardening #6.
- **S08-T12:** final bidirectional mapping, review, risks/limitations/retrospective and product-owner merge acceptance — D10 #194.

## Delivery index

- **S08-D01:** planning/readiness/tracker — PR #196; tracker #195.
- **S08-D02:** presence privacy contract — issue #186 / PR #197.
- **S08-D03:** deterministic map/provider boundary — issue #187 / PR #198.
- **S08-D04:** presence lifecycle/authorization composition — issue #188 / PR #199.
- **S08-D05:** browser map awareness — issue #189 / PR #200.
- **S08-D06:** mobile map awareness — issue #190 / PR #209; post-merge stale-test repairs #210/#211.
- **S08-D07:** accessible/degraded awareness — issue #191 / PR #212.
- **S08-D08:** physical microphone/location compatibility evidence — issue #192 / PR #215.
- **S08-D09:** hardening/performance/provider/license/cost evidence — issue #193 / PR #216.
- **S08-D10:** final traceability/review/product-owner acceptance — issue #194 / final review PR.

## Named hardening and performance evidence

Authoritative D09 head `7646f97679925daa5c00558def11870b1592e9a3` passed:

- normal CI run **#401** (`33293896181`);
- Sprint 7 hardening run **#73** (`33293896179`);
- Sprint 8 hardening run **#6** (`33293896184`).

The locked D09 synthetic matrix is 100 registered accounts / 25 presence viewers / 10
active publishers. Named Sprint 8 hardening evidence recorded:

- current-presence lookup/aggregation p95: **3.44 ms**;
- repeated presence refresh p95: **2.30 ms**;
- locked target: **400 ms p95** for both.

These are disposable PostGIS/CI control-plane measurements and are not claims about real
map-provider latency, physical GPS quality, mobile network behavior, media latency or
production capacity.

## Physical compatibility evidence boundary

S08-D08 recorded one real-system observation: on a physical MacBook, pressing **Start
RoadTalk** resulted in microphone and foreground location being reported enabled. The
subsequent session/account error was independent and led to #201/#202, followed by the
persistent registered-account correction in #207.

The following remain explicit **NOT PERFORMED / NOT AVAILABLE** evidence gaps:

- exact MacBook browser/version and separate localhost versus HTTPS-LAN runs;
- microphone denial/recovery and location denial/recovery on physical browser;
- physical receive/speaker path;
- physical iPhone browser and native-app microphone/location behavior;
- Android physical-device behavior;
- additional desktop OS/browser combinations.

Automated browser/mobile tests do not convert those rows into physical PASS claims.

## Provider/licensing/cost evidence boundary

No production map provider or map dataset was selected, downloaded, distributed or
activated. The repository supports only `disabled` and deterministic `fake` provider
behavior for this Sprint. A future production provider/dataset decision must separately
record license/attribution, privacy/data transfer, caching/offline/redistribution rules,
credentials, quotas/rates, recurring cost, update ownership and rollback/disable path.

Current/incremental recurring cost remains **$0 AWS + $0 LiveKit Cloud + $0 map/location
provider per month**. No payment-info free tier or spend-enabling provider account is
accepted by Sprint 8.

## Reverse traceability rule

Every Sprint 8 implementation artifact must map back to S08-R01–R12 and the locked
D01–D10 sequence. Anything that cannot be traced here is not retroactively authorized by
Sprint 8 and requires a later approved Sprint or dated decision.
