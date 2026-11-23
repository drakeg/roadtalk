# Sprint 16 D08 — Support, privacy, security, and legal preflight evidence

Issue: #483  
Requirement coverage: S16-R07, S16-R08, S16-R10, S16-R11  
Acceptance coverage: S16-T07, S16-T08, S16-T10, S16-T11

## Deterministic evidence

D08 adds a machine-readable, fail-closed preflight contract plus negative mutation tests. The contract requires support ownership/contact/coverage, inherited security/privacy release gates, retention/deletion review, concrete terms/privacy content, and unresolved-obligation recording.

The committed baseline intentionally reports `public_beta_ready: false` because named owners, published support contact/coverage, final retention/deletion review, final terms/privacy approval, and the legal-review decision are unresolved.

## Security and privacy

Existing Sprint 15 security/privacy controls remain authoritative: HIGH/CRITICAL actionable findings, privacy regressions, unsafe tracking/configuration, secret leakage, and unapproved exceptions block release. D08 does not weaken those controls.

## Retention and deletion

`docs/privacy/retention-deletion.md` consolidates current technical intent and explicitly identifies periods/policies that still require final approval. Backup remanence and deletion-after-restore obligations are disclosed as review requirements rather than hidden.

## Terms and privacy content

D08 creates review drafts under `docs/legal/` so the gate checks real content rather than a boolean-only promise. They are explicitly not approved and make no legal-counsel claim.

## Evidence limitations

No live support exercise, live privacy audit, legal-counsel review, public-beta launch, provider activation, real-money flow, DNS cutover, or recurring spend was performed or authorized by D08.
