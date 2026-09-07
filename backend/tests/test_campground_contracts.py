import pytest
from pydantic import ValidationError

from app.campgrounds.contracts import (
    PROHIBITED_CAMPGROUND_FIELDS,
    CampgroundAmenitySummary,
    CampgroundCommunicationContext,
    CampgroundPublicRecord,
    CampgroundSearchQuery,
)


def valid_record() -> dict[str, object]:
    return {
        "campground_id": "cg_finger_lakes_001",
        "name": "Finger Lakes Test Campground",
        "category": "state_park",
        "locality": "Ithaca",
        "region": "NY",
        "country_code": "US",
        "latitude": 42.45,
        "longitude": -76.52,
        "amenities": {
            "electric": True,
            "water": True,
            "dump_station": True,
            "pet_friendly": True,
        },
    }


def test_public_campground_contract_is_closed_and_source_is_deterministic() -> None:
    record = CampgroundPublicRecord.model_validate(valid_record())

    assert record.source == "deterministic_local"
    assert record.freshness == "deterministic"
    assert record.public_location_precision == "campground_centroid"
    assert isinstance(record.amenities, CampgroundAmenitySummary)

    with pytest.raises(ValidationError):
        CampgroundPublicRecord.model_validate({**valid_record(), "source": "live_provider"})


def test_public_contract_rejects_sensitive_presence_and_authorization_fields() -> None:
    for forbidden in sorted(PROHIBITED_CAMPGROUND_FIELDS):
        with pytest.raises(ValidationError):
            CampgroundPublicRecord.model_validate(
                {**valid_record(), forbidden: "attacker-controlled"}
            )


def test_search_contract_is_bounded_and_has_no_location_or_provider_overrides() -> None:
    query = CampgroundSearchQuery(query="lake", region="NY", amenity="electric", limit=25)
    assert set(query.model_dump()) == {"query", "category", "region", "amenity", "limit"}

    for forbidden in (
        "latitude",
        "longitude",
        "radius_m",
        "provider",
        "api_key",
        "recipient_ids",
        "occupancy_count",
        "visit_history",
    ):
        with pytest.raises(ValidationError):
            CampgroundSearchQuery.model_validate({"query": "lake", forbidden: "forbidden"})

    with pytest.raises(ValidationError):
        CampgroundSearchQuery(limit=101)


def test_campground_context_cannot_claim_authorization_source() -> None:
    context = CampgroundCommunicationContext(campground_id="cg_finger_lakes_001")
    assert context.context_only is True
    assert context.authorization_source == "existing_roadtalk_authorization"

    with pytest.raises(ValidationError):
        CampgroundCommunicationContext.model_validate(
            {
                "campground_id": "cg_finger_lakes_001",
                "context_only": False,
            }
        )

    with pytest.raises(ValidationError):
        CampgroundCommunicationContext.model_validate(
            {
                "campground_id": "cg_finger_lakes_001",
                "authorization_source": "campground_membership",
            }
        )


def test_campground_contract_does_not_expose_campsite_or_occupancy_semantics() -> None:
    public_fields = set(CampgroundPublicRecord.model_fields)
    assert not {
        "campsite_id",
        "campsite_number",
        "occupancy",
        "occupancy_count",
        "members",
        "member_ids",
        "arrival_at",
        "departure_at",
        "visit_history",
    }.intersection(public_fields)
