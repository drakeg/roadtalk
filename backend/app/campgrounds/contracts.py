from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CampgroundCategory = Literal[
    "public",
    "private",
    "state_park",
    "national_park",
    "county_municipal",
    "other",
]
CampgroundSource = Literal["deterministic_local"]
CampgroundFreshness = Literal["deterministic"]


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CampgroundAmenitySummary(ClosedModel):
    electric: bool = False
    water: bool = False
    sewer: bool = False
    dump_station: bool = False
    wifi: bool = False
    showers: bool = False
    laundry: bool = False
    pet_friendly: bool = False


class CampgroundPublicRecord(ClosedModel):
    campground_id: str = Field(min_length=8, max_length=64, pattern=r"^cg_[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=120)
    category: CampgroundCategory
    locality: str = Field(min_length=1, max_length=96)
    region: str = Field(min_length=1, max_length=64)
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    public_location_precision: Literal["campground_centroid"] = "campground_centroid"
    amenities: CampgroundAmenitySummary
    source: CampgroundSource = "deterministic_local"
    freshness: CampgroundFreshness = "deterministic"


PROHIBITED_CAMPGROUND_FIELDS = frozenset(
    {
        "account_id",
        "user_id",
        "recipient_id",
        "recipient_ids",
        "device_id",
        "installation_id",
        "username",
        "email",
        "phone",
        "password",
        "recovery_key",
        "access_token",
        "refresh_token",
        "provider",
        "provider_ref",
        "provider_key",
        "provider_token",
        "api_key",
        "campsite",
        "campsite_id",
        "campsite_number",
        "lot",
        "lot_number",
        "unit",
        "unit_number",
        "occupancy",
        "occupancy_count",
        "member_ids",
        "members",
        "present_users",
        "arrival_at",
        "departure_at",
        "visit_history",
        "location_history",
        "route",
        "corridor",
        "destination",
        "heading",
        "speed",
        "radius",
        "radius_m",
        "distance",
        "distance_m",
        "bearing",
        "audience",
        "audience_override",
    }
)


class CampgroundSearchQuery(ClosedModel):
    query: str | None = Field(default=None, min_length=1, max_length=96)
    category: CampgroundCategory | None = None
    region: str | None = Field(default=None, min_length=1, max_length=64)
    amenity: Literal[
        "electric",
        "water",
        "sewer",
        "dump_station",
        "wifi",
        "showers",
        "laundry",
        "pet_friendly",
    ] | None = None
    limit: int = Field(default=25, ge=1, le=100)


class CampgroundContextLabel(ClosedModel):
    campground_id: str = Field(min_length=8, max_length=64, pattern=r"^cg_[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=120)
    state: Literal["current", "unavailable"]


class CampgroundCommunicationContext(ClosedModel):
    campground_id: str = Field(min_length=8, max_length=64, pattern=r"^cg_[A-Za-z0-9_-]+$")
    context_only: Literal[True] = True
    authorization_source: Literal["existing_roadtalk_authorization"] = (
        "existing_roadtalk_authorization"
    )
