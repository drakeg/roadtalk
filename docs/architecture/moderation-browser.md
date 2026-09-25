# Browser moderation experience

Sprint 12 D06 exposes an authenticated browser safety console at `/safety` backed by closed moderation API schemas.

The browser can submit one bounded report reason, create a mute or block, list only the current account's active restrictions, and revoke only its own restriction by opaque restriction ID. It cannot submit narrative/evidence, coordinates, routes, media, recipient overrides, or moderation overrides.

All unavailable/missing/deleted/cross-owner restriction cases use generic moderation-unavailable responses. The page explicitly avoids claiming that a target exists and does not expose target profile, location, channel, convoy, device, report status, or enforcement details.

Destructive or consequential actions require browser confirmation. Status updates use an ARIA live region. If the moderation surface cannot load, the page states that existing server-side restrictions remain enforced rather than implying they were removed.

Report requests use the D05 account/device/peer/event limiter and D03 reporter-scoped idempotent persistence. Mute/block enforcement remains server-side in the D04 authorization filter.
