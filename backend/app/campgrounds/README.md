# Campgrounds backend package

Sprint 10 campground code is deliberately separated into public deterministic catalog data and ephemeral server-derived current context.

- `contracts.py` defines closed public/context contracts.
- `models.py` persists public campground catalog metadata only.
- `catalog.py` provides deterministic local/CI seed and bounded discovery.
- `context.py` derives a short-lived campground label only after existing RoadTalk current-location authorization succeeds.

Do not add user-campground history, campsite/unit presence, occupancy/member enumeration, client-selected campground authorization, external provider credentials/network calls, reservation/commerce state, or background location/audio to this package.
