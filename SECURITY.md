# Security Policy

## Reporting

Do not place credentials, tokens, personal data, exploit payloads, or sensitive production details in public issues. Use GitHub private vulnerability reporting through the repository Security interface when available. If private reporting is unavailable, contact the repository owner through a private channel before disclosing exploit details.

## Supported development line

Security fixes target the current `main` development line until versioned public releases establish a separate support matrix.

## Required controls

RoadTalk CI performs Python and mobile dependency auditing, secret/misconfiguration scanning, Terraform validation, container scanning, and project-specific security/privacy gates. High/critical actionable findings block acceptance unless a narrowly documented risk disposition is justified.

## Withdrawn advisory record

GitHub Advisory Database withdrew `GHSA-vfj7-8cjw-p6xm` (npm `braces`) on 2026-10-23 because it was not considered practically exploitable. npm audit can continue surfacing the historical advisory through Expo/Metro/Jest/React Native dependency paths. RoadTalk classifies that exact withdrawn advisory as non-blocking while continuing to block any other high/critical advisory in those paths. This is an advisory-specific disposition, not a package-wide exception.

## Release security

Do not publish a release while required security checks fail. Security fixes may justify an expedited PATCH release after the exact release commit passes the required validation.
