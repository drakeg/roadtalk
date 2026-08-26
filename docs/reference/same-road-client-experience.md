# Same-road client experience

Sprint 7 keeps **Nearby** as the default audience mode. **Same road** is an explicit, restrictive option that can only narrow the already-authorized nearby audience.

## Mobile

Authenticated users can open **Audience mode** from the RoadTalk home screen and select Nearby or Same road. The client loads the server-authoritative mode and version from `GET /api/v1/me/route-mode` and updates it through `PUT /api/v1/me/route-mode`.

Before a mode change, the mobile client uses the existing safe media-transition boundary to stop current media activity. It resumes through that same lifecycle after the server update completes. Version conflicts and other failures are shown generically without route or eligibility detail.

The only route-awareness states shown to a user are generic states such as:

- Nearby is active
- Same road is active
- Matching
- Same road is unavailable
- RoadTalk could not update your audience mode

## Browser

The local Web Radio session can open `/audience`. This page shares the browser session stored by the existing Web Radio flow, supports the same Nearby/Same-road API contract, and links back to `/`.

The browser validates the minimized response before rendering it. Responses containing road names, provider/corridor references, corridor digests, directions, coordinates, exact distance, bearing, identity fields, participant references, or eligibility reasons are rejected generically.

## Privacy and safety boundary

Clients do not display or persist a road name, route, provider, corridor, direction, coordinate, exact distance, bearing, nearby identity, participant identity, or eligibility reason. They do not add maps, markers, destination entry, navigation, background location/audio, hands-free control, notifications, provider activation, or automatic subscription.

Same-road failure is fail-closed. If route context is unavailable, the client must not silently widen the user's audience back to Nearby. Nearby behavior remains unchanged when Nearby is explicitly selected.
