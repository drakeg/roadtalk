# Browser convoy experience

Sprint 11 D06 exposes a browser experience at `/convoys` backed by authenticated, closed-schema lifecycle endpoints under `/api/v1/convoys`.

The page supports current status, create, join, member leave, leader disband, and privacy-safe current awareness. Leave and disband require explicit browser confirmation. Controls are disabled while a mutation is pending, status changes use an ARIA live region, keyboard focus is visible, and degraded awareness does not remove lifecycle controls.

The API accepts only convoy display name or convoy ID where required; extra request fields are rejected. Status exposes only convoy ID, membership ID, display name, role and active state. Awareness uses the D05 bounded contract. No browser response exposes coordinates, routes, movement history, device/session identifiers, provider credentials, or authorization reasons.

Convoy membership remains context only. Existing RoadTalk account/session/location/channel/proximity/Same-road/media authorization remains authoritative. D06 adds no external provider, cloud resource, background location/audio, analytics, payment, or recurring spend. Incremental recurring cost remains $0.
