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
  unapproved managed-service dependencies. Run both locally before opening a pull
  request; GitHub CI runs them again in the security job.
