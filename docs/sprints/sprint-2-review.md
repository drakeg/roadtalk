# Sprint 2 review record

- Sprint: 2 — Identity
- Status: Approved upon merge of this review
- Review date: 2026-07-14
- Deliverable: S02-D10
- Issue: #60
- Acceptance: S02-T11 and S02-T12

## Decision requested

Merging this review records product-owner approval of the completed Sprint 2
repository/CI scope and authorizes Sprint 3 planning. It does not authorize a field
test, close Sprint 1 exceptions, or claim any unperformed device or AWS procedure.

## Review outcome

S02-D01 through S02-D09 are merged. The implementation provides an optional public
identity with a unique callsign and bundled avatar, plus optional PII-free anonymous
recovery. The database, API, mobile experience, privacy/security hardening, regression
gates, and operator documentation were reviewed against the approved specification.

All automated acceptance evidence is green. The product-owner decision becomes
**APPROVED** when this review pull request is merged. The Sprint 2 tracker may then
close and Sprint 3 planning may begin.

## Demonstration record

Demonstrated with synthetic data through CI and repository review:

- anonymous registration and incomplete private profile state
- deterministic callsign validation, reserved/confusable rejection, availability,
  uniqueness, cooldown, and mutation limits
- owner-only conditional profile updates and stale-version conflict handling
- versioned bundled-avatar selection, retained retired rendering, and accessibility
- mobile setup/settings loading, offline, retry, unavailable, and conflict states
- optional recovery-key creation and one-time display
- account transfer to an eligible fresh installation, replacement-key rotation,
  old-session revocation, and replay rejection
- constant-shape recovery failures and bounded abuse dimensions
- closed-field logs, route templates, exact OpenAPI contracts, and privacy/scope gates
- full Sprint 1 backend, migration, mobile, dependency, container, and zero-resource
  Terraform regression suite

The detailed step-to-test mapping is in
[Sprint 2 synthetic identity evidence](../evidence/sprint-2/README.md).

Not demonstrated and not claimed:

- installed iOS or Android development builds on physical devices
- native Keychain/Keystore and backup inspection
- clean-machine end-to-end setup
- an enabled AWS plan or deployed field-test environment
- production/multi-worker shared rate limiting
- backup/restore, alarm, budget, or operational AWS rehearsal

## Acceptance results

| Test group | Result | Review evidence |
|---|---|---|
| S02-T01–T04 persistence, policy, API, avatars | PASS | Live PostgreSQL migrations/lifecycle, contract, catalog, and accessibility tests |
| S02-T05 mobile identity | PASS | Expo Doctor, strict TypeScript, Jest setup/settings/error/accessibility tests |
| S02-T06 recovery lifecycle | PASS | Synthetic transfer, rotation, revocation, replay, and replacement-session tests |
| S02-T07 recovery privacy | PASS | Constant-shape HTTP, leakage injection, storage, URL, log, and UI tests |
| S02-T08 abuse limits | PASS | Availability, mutation, peer, installation, selector, account, and device limiter tests |
| S02-T09 Sprint 1 regression | PASS | Backend/PostGIS/migration, mobile, security, container, and Terraform jobs |
| S02-T10 contracts/scope | PASS | Exact OpenAPI, dependency, permission, privacy allowlist, and later-sprint audit |
| S02-T11 synthetic demonstration | PASS | Composed lifecycle evidence with synthetic data and no field-test claim |
| S02-T12 review | APPROVED UPON MERGE | Traceability, cost/privacy review, limitations, retrospective, and this decision |

See [Sprint 2 traceability and evidence](sprint-2-traceability.md) for the complete
requirement-to-test-to-deliverable mapping.

## Definition of Done

- [x] S02-R01 through S02-R12 implemented and traced
- [x] S02-T01 through S02-T11 pass with privacy-safe evidence
- [x] S02-D01 through S02-D09 merged
- [x] backend/PostgreSQL/migrations, mobile, security, container, and IaC gates pass
- [x] identity and optional recovery lifecycle demonstrated with synthetic data
- [x] no raw recovery key, unauthorized field, callsign log content, location, or
  audio data is collected or leaked by the approved implementation
- [x] no AWS resource or recurring infrastructure cost introduced
- [x] known limitations and evidence boundaries recorded
- [ ] S02-D10 review merged and S02-T12 product-owner approval effective
- [ ] Sprint 2 tracker closed as completed

The final two boxes are completed operationally after this review is merged; they
must not be represented as complete beforehand.

## Cost decision

Sprint 2 introduced application code and existing-database rows only. Bundled avatar
assets ship with the application and backend container. CI uses no AWS credentials,
and Terraform remains disabled by default with zero-resource guards.

**Approved incremental AWS cost: $0.** Do not add RDS, managed Redis, NAT Gateway,
ALB, Fargate, Cognito, SES, SNS, Pinpoint, Lambda, S3, CloudFront, image processing,
additional compute, or another managed service without a separate written scope and
cost decision supported by measured need.

## Known limitations and accepted design boundaries

- Callsigns are public pseudonyms and are not verified real-world identities.
- A lost recovery key cannot be recovered by support; the existing device remains
  authoritative until a new key is created.
- Device SecureStore is optional, off by default, and does not transfer a key to a
  new device; users need their own private external copy.
- Recovery and mutation limiters are process-local for the approved single-worker
  design. Multi-worker scaling requires a reviewed shared-control and cost decision.
- Pepper rotation invalidates existing recovery keys because plaintext keys are never
  retained and hashes cannot be re-peppered.
- Installed-device accessibility, native storage, backup, and OS screenshot behavior
  still require device evidence.
- S01-E01 through S01-E03 remain hard blockers for any field test.
- Production scale, availability, moderation, legal/store, and later-sprint features
  remain out of scope.

## Retrospective

What worked:

- small requirement-linked deliverables with complete CI on every pull request
- a minimal public DTO and bundled assets that prevented media-service scope growth
- privacy and abuse controls delivered with the features they protect
- recovery designed without contact PII, hosted identity, support bypass, or messaging
- exact OpenAPI, dependency, permission, and log allowlists that fail on scope drift
- repeated zero-resource Terraform and cost gates

Improvements:

- add one named cross-layer lifecycle test earlier instead of composing final evidence
  from several focused tests
- schedule physical-device accessibility and native-storage audits before a future
  sprint review when hardware becomes available
- reduce connector-created one-file commits when authenticated batch publication is
  available
- evaluate a shared limiter only after measurements show more than one API worker is
  necessary
- keep merge-bound product-owner decisions explicit so evidence never claims approval
  before it occurs

## Approval decision and next action

**Decision: approved upon merge.** Merging this review completes S02-D10 and S02-T12,
authorizes closing issue #60 and tracker #61, and permits Sprint 3 planning. It does
not authorize Sprint 3 coding before a separate specification/readiness approval, and
it does not authorize a field test while S01-E01 through S01-E03 remain open.
