# Map provider boundary

Sprint 8 D03 introduces a deterministic map-rendering provider boundary without selecting or activating a production map, tile, geocoding, routing, traffic, or location service.

## Accepted local/CI provider

The only enabled implementation for Sprint 8 acceptance is `FakeMapTileProvider`. It generates deterministic 256×256 SVG fixture tiles from validated `z/x/y` tile coordinates. It performs no network request, reads no map/road dataset, requires no URL, API key, token, account, payment method, or recurring service, and discloses no RoadTalk user location to an external party.

The default provider is disabled and fails closed.

`MapTileFetcher` adds a timeout, provider-version check, SVG-only content-type check, and tile-size bound around any configured provider implementation. Provider exceptions are converted to the stable non-disclosing `map provider unavailable` failure.

## Privacy relationship

This boundary is intentionally independent of the D02 presence privacy policy. A map tile is background orientation content; it is not an authorization input and contains no account, device, callsign, current location, presence-cell membership, route context, channel, or media eligibility data.

Future browser/mobile work may compose the user's own accepted foreground location and D02-approved coarse nearby-presence cells over this map surface. A map provider may never broaden Nearby/Same-road/channel/session/grant authorization.

## Production activation gate

No production/public provider is approved by this deliverable. Before adding or enabling one, a separate dated product-owner decision must record at minimum:

- provider/dataset identity and geographic scope;
- license and attribution obligations and exact attribution placement;
- derivative/share-alike obligations, if any;
- provider privacy terms and what request metadata leaves RoadTalk;
- retention, caching, offline, proxying, and redistribution rules;
- quotas, rate limits, abuse controls, availability, and support expectations;
- API-key/token handling and rotation, if credentials are required;
- update/version process and operational owner;
- expected recurring cost, hard spend controls, and rollback/exit path.

Public OpenStreetMap tile services or any other community/public endpoint must not be treated as free production infrastructure merely because it can be reached without payment.

## Failure behavior

- Disabled provider: map background unavailable; existing radio/location/presence authorization is unaffected.
- Invalid tile request: rejected before provider execution.
- Provider timeout/error: converted to a stable unavailable result; no provider detail is exposed.
- Invalid provider version/content type/oversized tile: rejected by the fetcher.
- Provider outage must degrade only the visual map background. It must not invent stale precision or change communication eligibility.

## Sprint boundary

D03 does not add a public tile endpoint, browser/mobile map UI, presence lifecycle, database table, external network request, background tracking, AWS/LiveKit Cloud resource, paid service, or recurring spend. Those remain governed by the Sprint 8 locked sequence and named activation exceptions.
