# Sprint 10 D04 campground presence evidence

## Scope

D04 implements S10-R04–R05 and S10-T04–T05 only. It derives ephemeral campground labels from existing authorized current-location state and adds no new authorization source, persistent user-campground relationship, provider activation, or spend.

## Requirement mapping

- **S10-R04 / S10-T04:** `backend/app/campgrounds/context.py` gates derivation on active account, usable/unexpired current location, matching current consent policy, latest granted consent, and an active source-device session. No client campground ID is accepted by the derivation entry point.
- **S10-R05 / S10-T05:** derived output is a campground label plus inherited current-location expiry. Tests assert that campsite, occupancy, membership, distance, audience, recipient and account identity are absent. No campground-presence/history persistence is introduced.

## Fail-closed behavior

The authoritative query returns no current point when account, consent, session, location quality, policy version, or expiry requirements fail. With no authorized current point there is no campground context. Context expiration is inherited directly from current location rather than extended by campground logic.

## Authorization non-broadening

D04 does not modify channel, proximity, Same-road, media, notification, recipient, publisher, or listener eligibility. The campground result can be consumed later as descriptive/narrowing context only; it cannot convert an upstream denial into authorization.

## Evidence limitations

The deterministic centroid-distance policy is local/CI test behavior only. D04 does not claim real campground boundary accuracy, live occupancy, provider freshness/completeness, physical-device campground detection, production behavior, or external-provider behavior. Current and incremental recurring cost remains $0.
