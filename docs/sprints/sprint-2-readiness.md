# Sprint 2 readiness

- Sprint: 2 — Identity
- Status: READY upon specification approval
- Planning issue: #49
- Readiness date: 2026-07-13
- Baseline: Sprint 1 conditional-acceptance merge `9126c9669b53448ea3b532fd5b13221f4a5f0633`

## Decision

Sprint 2 is ready to begin after the Identity specification pull request is merged.
The sprint can be implemented entirely through local development and GitHub CI,
without enabling AWS resources or closing any Sprint 1 accepted exception.

## Definition of Ready

- [x] Roadmap objective is explicit: anonymous auth, profile, callsign, avatar.
- [x] Requirements, acceptance tests, deliverables, order, and exit criteria are
  defined in the proposed specification.
- [x] Profile, API, database, security, privacy, and mobile architecture dependencies
  are already approved.
- [x] Callsign normalization, enumeration, concurrency, and abuse risks are bounded.
- [x] Avatar scope is limited to bundled assets; uploads and cloud media services are
  excluded.
- [x] Recovery is optional, PII-free, and bounded by one-time high-entropy keys.
- [x] Later-sprint location, audio, channel, moderation, notification, and production
  behavior is explicitly excluded.
- [x] Sprint 1 regressions remain required acceptance evidence.
- [x] No new AWS resource or recurring infrastructure cost is authorized.
- [x] Planning approval and implementation authorization are separated.

## Preconditions before the first code change

1. Merge the Sprint 2 specification pull request to record product-owner approval.
2. Close planning issue #49 as completed.
3. Create one Sprint 2 tracker and S02-D01 through S02-D10 issues from the exact
   merged specification.
4. Update the documentation index and repository status to make Sprint 2 the sole
   active implementation sprint.
5. Start S02-D01 from the specification merge commit using the normal branch/PR
   workflow.

## Cost gate

The default and expected incremental AWS cost for Sprint 2 is **$0**. Development
uses the existing local PostgreSQL/PostGIS service and GitHub CI. Field-test
Terraform remains disabled. Any proposal for object storage, CDN, email/SMS,
identity-as-a-service, image analysis, additional compute, or another managed
service is a scope change requiring a written cost decision before implementation.

## Sprint 1 exception boundary

S01-E01 through S01-E03 remain open and must close before any field-test environment
is enabled or distributed. Sprint 2 local/CI work must not imply those rehearsals
were executed or their risks resolved.

## Readiness conclusion

**READY upon merge.** There is no unresolved technical or cost decision blocking the
defined local/CI implementation. Merge approval locks the Sprint 2 baseline; later
changes require the repository change-control process.
