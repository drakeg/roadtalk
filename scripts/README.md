# Scripts

Cross-project helper scripts belong here only when an approved deliverable requires them.

Scripts must:

- be non-interactive by default where automation uses them
- fail on errors
- avoid printing secrets or sensitive data
- document required inputs and side effects
- have tests or a documented validation method
- avoid duplicating standard package-manager or Terraform commands without a clear reason

## CI privacy gates

- `scripts/ci/check-identity-privacy.py` rejects Sprint 2 identity/recovery scope drift.
- `scripts/ci/check-location-privacy.py` rejects background location, coordinate
  persistence/logging paths, maps/geocoding, location history, paid providers, and
  unapproved managed-service dependencies.
- `scripts/ci/check-ptt-privacy.py` rejects live provider configuration/network paths,
  over-scoped or paid media capabilities, background/camera/media persistence paths,
  token/secret/audio/transcript logging or evidence, later-sprint proximity/channel
  drift, and non-metadata grant columns.
- `scripts/ci/check-ptt-operations.py` requires the approved PTT stop ceilings,
  activation/revocation/destroy procedures, named live/device exceptions, a $10
  Terraform notification budget, zero-resource defaults, and CI enforcement.
- `scripts/ci/check-sprint-4-review.py` requires complete S04-R01–R12,
  S04-T01–T12, and S04-D01–D09 traceability; merge-bound product-owner approval;
  honest live/device exceptions; $0 current cost; and synthetic 100/25/10 grant-scale
  measurement against the 250 ms p95 target.
- `scripts/ci/check-sprint-5-planning.py` locks the approved S05-R01–R12,
  S05-T01–T12, and S05-D01–D09 scope; default-deny selective subscription;
  non-persistence of recipient membership; the 100/25/10 and 400 ms targets; named
  field exceptions; and $0/no-new-service planning boundaries before approval.
- `scripts/ci/check-proximity-privacy.py` locks the Sprint 5 server-owned policy,
  usable-through-expiry receiver join, indexed `ST_DWithin` operation, exact transient
  opaque result shape, default-deny selective-subscription provider contracts,
  exact publication API/metadata shape, provider-disabled defaults, and no-new-service
  boundary.
- `scripts/ci/check-sprint-6-planning.py` locks approved S06-R01–R12, S06-T01–T12,
  S06-D01–D09, General/RV/private semantics, one-time invite security, channel-bound
  proximity/media authority, 100/25/10 and 400 ms targets, named exceptions, READY
  status, approval/tracker records, and $0/no-new-service boundaries.
- `scripts/ci/check-channel-privacy.py` locks deterministic General/RV seeds,
  one-per-account selection, active private-membership catalog authorization, required
  media-grant channel binding, exact caller-scoped routes, non-disclosing schemas,
  serialized fail-closed switching, and the no-provider/no-new-service boundary.
- `scripts/ci/check-channel-hardening.py` requires the S06-D08 multi-channel 100/25/10
  scale test, channel/invite/race/privacy coverage, the channel operations and evidence
  records, disabled Terraform validation, and no new paid or later-sprint dependencies.

Run every gate locally before opening a pull request; GitHub CI runs them again in the
security job.
