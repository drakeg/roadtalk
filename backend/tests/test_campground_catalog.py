from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.campgrounds.catalog import search_catalog, seed_deterministic_catalog
from app.campgrounds.contracts import CampgroundSearchQuery
from app.campgrounds.models import Campground
from app.db.base import Base


def test_campground_model_contains_no_account_presence_or_provider_fields() -> None:
    columns = set(Campground.__table__.columns.keys())
    assert not {
        "account_id",
        "user_id",
        "device_id",
        "campsite_id",
        "campsite_number",
        "occupancy",
        "occupancy_count",
        "visit_history",
        "provider",
        "provider_ref",
        "api_key",
        "route",
        "destination",
    }.intersection(columns)


def test_catalog_seed_is_deterministic_and_idempotent() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Campground.__table__.create(engine)

    with Session(engine) as session:
        assert seed_deterministic_catalog(session) == 2
        assert seed_deterministic_catalog(session) == 0
        session.commit()

        records = search_catalog(session, CampgroundSearchQuery(region="NY"))
        assert [record.campground_id for record in records] == ["cg_finger_lakes_001"]
        assert records[0].source == "deterministic_local"
        assert records[0].freshness == "deterministic"


def test_catalog_search_is_bounded_and_filters_metadata_only() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Campground.__table__.create(engine)

    with Session(engine) as session:
        seed_deterministic_catalog(session)
        session.commit()

        records = search_catalog(
            session,
            CampgroundSearchQuery(query="test", amenity="sewer", limit=1),
        )
        assert len(records) == 1
        assert records[0].campground_id == "cg_central_pa_001"


def test_campground_metadata_is_registered_without_user_relationships() -> None:
    assert "campground" in Base.metadata.tables
    table = Base.metadata.tables["campground"]
    assert not table.foreign_keys
