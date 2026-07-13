# Sprint 2: Identity

## Status

Approved upon merge of the specification pull request.

## Objective

Give every anonymous RoadTalk account a safe, editable public identity consisting of
a unique callsign and a bundled avatar, plus an optional privacy-preserving recovery
key, while preserving the Sprint 1 session model and collecting no email address,
phone number, location, audio, or user-uploaded media.

## Product decisions

- A callsign is required before identity setup is complete.
- Avatars are selected from a versioned catalog bundled with the mobile application.
  Sprint 2 does not accept user-uploaded images.
- Anonymous recovery is optional and uses a high-entropy recovery key. RoadTalk stores
  only a slow hash and never sends the key by email or SMS.
- A successful recovery transfers the account to the new registered device, rotates
  the recovery key, and revokes existing sessions.
- Public identity exposes only the display callsign and approved avatar identifier.
  Account, device, session, recovery, and moderation fields remain private.
- Callsign changes use optimistic concurrency and a cooldown to reduce impersonation
  and abuse. Exact rate and cooldown values are server configuration, not public API
  promises.

These choices satisfy the roadmap's profile, callsign, avatar, and anonymous-account
continuity goals without object storage, image processing, CDN, email, SMS, or a new
AWS service.

## Requirements

- **S02-R01 — Profile persistence:** Add a one-to-one profile for each account with
  normalized/display callsign, bundled avatar identifier, setup state, version,
  timestamps, and database-enforced ownership and uniqueness.
- **S02-R02 — Callsign policy:** Define deterministic Unicode-aware normalization,
  allowed characters, length, reserved names, confusable handling, uniqueness, and
  stable validation problems. Store the normalized value separately from display.
- **S02-R03 — Callsign availability:** Provide an authenticated, rate-limited
  availability check that returns only available/unavailable plus a stable reason and
  never identifies the owning account.
- **S02-R04 — Private profile API:** Implement authenticated profile read and
  conditional update endpoints. Updates are atomic, reject stale versions, and never
  allow account/session/security fields to be changed through profile input.
- **S02-R05 — Public identity contract:** Provide the minimal identity representation
  needed by later sprints: display callsign and catalog avatar only. Exact location,
  account/device/session identifiers, recovery state, and internal moderation state
  are excluded.
- **S02-R06 — Bundled avatar catalog:** Define a versioned, accessible avatar catalog
  shipped in the application and validated by the backend. Unknown or retired avatar
  identifiers fail closed; retained selections remain renderable.
- **S02-R07 — Identity mobile experience:** Add setup and settings flows for callsign
  validation, availability, avatar selection, save conflicts, retry, offline/error
  states, and accessibility. Authentication remains usable when setup is incomplete,
  but later identity-dependent features can detect that state.
- **S02-R08 — Optional anonymous recovery:** Allow a user to create a cryptographically
  random recovery key, display it once, store only its slow hash server-side, and
  restore the account on a newly registered device without collecting contact PII.
- **S02-R09 — Recovery containment:** Rate-limit recovery attempts; use constant-shape
  failure responses; rotate the recovery key; revoke old sessions on success; prevent
  replay; and keep recovery secrets out of logs, analytics, URLs, crash data, and
  ordinary device storage.
- **S02-R10 — Identity privacy and abuse controls:** Prevent enumeration through
  availability/recovery responses, reserve system-like callsigns, add configurable
  mutation limits, and log only allowlisted technical events without callsign or
  recovery-key content.
- **S02-R11 — Compatibility and migration:** Add backward-compatible database/API
  changes, migrate existing anonymous accounts without inventing public identities,
  and preserve Sprint 1 registration, refresh, logout, revocation, deployment, and
  rollback behavior.
- **S02-R12 — Quality and evidence:** Extend backend, migration, mobile, OpenAPI,
  security, privacy, and scope-protection tests; update operator/user documentation;
  and record requirement-to-test evidence and the Sprint 2 review decision.

## Out of scope

- user-uploaded photos, image moderation, S3 avatar objects, CDN delivery, or image
  transformation
- email, SMS, social login, password login, verified real-world identity, or contact
  discovery
- display name, biography, social links, vehicle information, badges, reputation, or
  public profile search
- location permissions/collection, nearby discovery, maps, heading, or speed
- microphone permissions, push-to-talk, audio transport, recording, or transcription
- channels, presence, notifications, convoys, campground features, moderation UI,
  subscriptions, AI, or production scaling
- enabling AWS resources or executing Sprint 1 acceptance-exception rehearsals

## API baseline

The exact OpenAPI schema is delivered with implementation, but Sprint 2 reserves:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/me/profile` | GET | Read the authenticated account's identity/setup state. |
| `/api/v1/me/profile` | PATCH | Conditionally update callsign/avatar. |
| `/api/v1/callsigns/availability` | GET | Check normalized availability without owner disclosure. |
| `/api/v1/avatars` | GET | Read the supported catalog version and identifiers. |
| `/api/v1/me/recovery-key` | POST | Create or rotate a recovery key and return it once. |
| `/api/v1/sessions/recover` | POST | Recover an anonymous account and establish a new session. |

Profile mutations require the current resource version. Recovery success returns the
normal Sprint 1 session response plus a replacement recovery key; recovery failure
does not distinguish unknown, expired, replayed, or invalid keys.

## Acceptance tests

| Test ID | Requirements | Procedure | Expected result |
|---|---|---|---|
| S02-T01 | R01, R11 | Upgrade empty and Sprint 1 databases; inspect constraints; downgrade/forward-fix where safe. | Existing accounts remain private/incomplete, profile invariants hold, and migration checks pass. |
| S02-T02 | R02, R03, R10 | Exercise case, whitespace, Unicode normalization, length, reserved/confusable values, collisions, and availability throttling. | Equivalent callsigns cannot collide; invalid values return stable problems; owners are never disclosed. |
| S02-T03 | R04, R05 | Read/update profiles as owner and attempt missing auth, cross-account access, unknown fields, and stale versions. | Authorized atomic updates succeed; unauthorized, over-posted, and stale writes fail closed. |
| S02-T04 | R06 | Compare mobile catalog assets/metadata with backend validation; test active, retired, and unknown identifiers. | Supported avatars render accessibly; retired selections remain safe; unknown values are rejected. |
| S02-T05 | R07 | Run setup/settings mobile tests for loading, valid, invalid, unavailable, conflict, offline, retry, and screen-reader labels. | The flow is deterministic, accessible, and exposes no later-sprint permissions or screens. |
| S02-T06 | R08, R09 | Create a recovery key, recover on a second device, retry the old key, and use pre-recovery sessions. | Recovery works once; a replacement key is issued; replay and old sessions fail. |
| S02-T07 | R09, R10 | Inject invalid/unknown/replayed keys and inspect response shapes, logs, errors, URLs, analytics mocks, and ordinary storage. | Attempts are bounded and non-enumerating; no recovery secret or callsign content leaks. |
| S02-T08 | R10 | Exceed configured availability, mutation, and recovery limits from account/device/network dimensions. | Stable 429 problems and Retry-After are returned without publishing exact abuse thresholds. |
| S02-T09 | R11 | Re-run the complete Sprint 1 backend, PostGIS, mobile, security, container, and zero-resource Terraform gates. | Existing authentication and operational foundations remain green. |
| S02-T10 | R12 | Validate OpenAPI, generated/static client types, dependency scans, privacy allowlists, and later-sprint scope audit. | Contracts agree, scans pass, and no location/audio/channel/cloud expansion is introduced. |
| S02-T11 | R01–R12 | Demonstrate registration, identity setup, conflict handling, avatar selection, recovery transfer, settings edit, and revocation. | The complete identity lifecycle works with synthetic data and documented evidence. |
| S02-T12 | R12 | Review traceability, documentation, cost posture, known limitations, and retrospective. | Every requirement maps to passing evidence and the product owner records the sprint decision. |

## Deliverables

- **S02-D01:** Approved Identity specification, readiness record, tracker, and scoped
  implementation issues.
- **S02-D02:** Profile schema/model and backward-compatible migration.
- **S02-D03:** Callsign normalization, policy, availability, and abuse controls.
- **S02-D04:** Authenticated private/public identity API contracts and services.
- **S02-D05:** Bundled avatar catalog, backend validation, and accessible assets.
- **S02-D06:** Mobile identity setup and settings experience.
- **S02-D07:** Optional recovery-key backend lifecycle and security controls.
- **S02-D08:** Mobile recovery-key creation, one-time display, and recovery experience.
- **S02-D09:** Identity privacy/security hardening, regression gates, and runbooks.
- **S02-D10:** Traceability, demonstration evidence, sprint review, and retrospective.

## Implementation order

1. D01 specification/readiness/tracker
2. D02 profile persistence
3. D03 callsign policy and availability
4. D04 profile/identity API
5. D05 bundled avatar catalog
6. D06 mobile identity experience
7. D07 recovery backend
8. D08 recovery mobile experience
9. D09 hardening and documentation
10. D10 evidence and sprint review

Only one code deliverable should be in progress unless dependencies make independent
parallel work explicit.

## Dependencies

- Sprint 1 conditional acceptance and merge commit
  `9126c9669b53448ea3b532fd5b13221f4a5f0633`.
- Sprint 1 exceptions S01-E01 through S01-E03 remain hard blockers for a field test,
  but not for local/CI Sprint 2 implementation.
- Existing FastAPI, SQLAlchemy/Alembic, PostgreSQL/PostGIS, Expo/React Native,
  SecureStore, CI, container, and disabled Terraform foundations.
- No new cloud dependency is required.

## Entry criteria

- Sprint 1 tracker is closed and its conditional acceptance is recorded.
- This specification is reviewed and merged.
- D01 tracker/issues are created from the merged wording.
- The first code branch starts from the specification merge commit.
- No AWS resource is enabled and no Sprint 1 exception is represented as closed.

## Exit criteria

- S02-R01 through S02-R12 are implemented.
- S02-T01 through S02-T12 pass with privacy-safe evidence.
- S02-D01 through S02-D10 are merged and the tracker is complete.
- Identity setup and optional recovery are demonstrated on synthetic accounts.
- Sprint 1 regressions remain green.
- No raw recovery key, unauthorized public field, location, or audio data is
  collected or leaked.
- No new AWS service or recurring infrastructure cost is introduced.
- Sprint 2 review is approved before Sprint 3 planning begins.

## Cost posture

Sprint 2 adds application code and rows to the existing PostgreSQL database only.
Bundled avatar assets ship with the mobile app and backend container. Recovery uses
existing API/database capacity and local cryptography. Terraform must continue to
plan zero resources by default. No S3 avatar bucket, CloudFront distribution, Lambda,
SES, SNS messaging, Pinpoint, Cognito, Rekognition, RDS, managed cache, or additional
compute is authorized.

If measured field-test load later justifies a change, it requires a separate
documented decision and cost review.

## Security and privacy constraints

- Recovery keys require at least 256 bits of cryptographic randomness and slow,
  versioned server-side hashing with a separately stored application pepper.
- The plaintext recovery key is returned only at creation/successful recovery and is
  never retrievable afterward.
- Mobile may place a recovery key in platform-secure storage only after explicit user
  choice; it must never use AsyncStorage, logs, analytics, clipboard by default, URL
  parameters, or screenshots generated by the app.
- Callsigns are public pseudonyms. The UI must explain this before save.
- Callsign and recovery endpoints use authentication/rate limits appropriate to their
  enumeration risk; recovery itself is unauthenticated but tightly bounded.
- Structured logs record request ID, route template, result class, duration, and
  stable problem code only—not callsign text, recovery material, or request bodies.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Callsign squatting or impersonation | Trust and abuse harm | Reserved/confusable policy, cooldown, mutation limits, later moderation compatibility |
| Recovery-key theft | Account takeover | High entropy, one-time display, slow hash, no contact channel, rotation, session revocation, leakage tests |
| User loses recovery key | Anonymous identity cannot be restored | Clear disclosure; existing device remains authoritative; no insecure support bypass |
| Unicode inconsistency | Collisions or unusable names | One shared test corpus, server authority, database normalized uniqueness |
| Avatar scope expands into media service | Cost, privacy, moderation burden | Bundled catalog only; uploads require a future approved change |
| Public response leaks internal identity | Privacy/security exposure | Explicit response DTOs, authorization tests, allowlist logging |
| Sprint 1 exceptions are forgotten | Field-test risk | Keep pre-field-test hard stop and do not close exceptions from Sprint 2 evidence |
