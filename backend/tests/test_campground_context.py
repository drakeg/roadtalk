from datetime import UTC, datetime, timedelta

from app.campgrounds.catalog import _model_from_record
from app.campgrounds.context import AuthorizedCurrentPoint, match_current_campground
from app.campgrounds.contracts import CampgroundAmenitySummary, CampgroundPublicRecord


def _campground(*, campground_id: str, latitude: float, longitude: float):
    return _model_from_record(
        CampgroundPublicRecord(
            campground_id=campground_id,
            name=f"{campground_id} Test Campground",
            category="public",
            locality="Testville",
            region="PA",
            country_code="US",
            latitude=latitude,
            longitude=longitude,
            amenities=CampgroundAmenitySummary(),
        )
    )


def test_current_context_is_ephemeral_label_only() -> None:
    expires_at = datetime.now(UTC) + timedelta(minutes=5)
    context = match_current_campground(
        AuthorizedCurrentPoint(latitude=40.7901, longitude=-77.8601, expires_at=expires_at),
        [_campground(campground_id="cg_test_001", latitude=40.79, longitude=-77.86)],
    )

    assert context is not None
    assert context.expires_at == expires_at
    assert context.label.model_dump() == {
        "campground_id": "cg_test_001",
        "name": "cg_test_001 Test Campground",
        "state": "current",
    }
    serialized = context.label.model_dump()
    assert "account_id" not in serialized
    assert "occupancy" not in serialized
    assert "members" not in serialized
    assert "campsite" not in serialized


def test_context_does_not_exist_outside_deterministic_match() -> None:
    point = AuthorizedCurrentPoint(
        latitude=40.0,
        longitude=-75.0,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    context = match_current_campground(
        point,
        [_campground(campground_id="cg_test_002", latitude=42.45, longitude=-76.52)],
    )
    assert context is None


def test_nearest_deterministic_context_wins_without_exposing_distance() -> None:
    expires_at = datetime.now(UTC) + timedelta(minutes=5)
    context = match_current_campground(
        AuthorizedCurrentPoint(latitude=40.79, longitude=-77.86, expires_at=expires_at),
        [
            _campground(campground_id="cg_test_far", latitude=40.80, longitude=-77.86),
            _campground(campground_id="cg_test_near", latitude=40.7901, longitude=-77.86),
        ],
    )

    assert context is not None
    assert context.label.campground_id == "cg_test_near"
    assert "distance" not in context.label.model_dump()


def test_context_has_no_client_presence_or_authorization_input() -> None:
    fields = set(AuthorizedCurrentPoint.__dataclass_fields__)
    assert fields == {"latitude", "longitude", "expires_at"}
    assert "campground_id" not in fields
    assert "audience" not in fields
    assert "recipient_ids" not in fields
