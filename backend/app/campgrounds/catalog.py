from collections.abc import Iterable

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.campgrounds.contracts import CampgroundAmenitySummary, CampgroundPublicRecord, CampgroundSearchQuery
from app.campgrounds.models import Campground

DETERMINISTIC_CAMPGROUNDS: tuple[CampgroundPublicRecord, ...] = (
    CampgroundPublicRecord(
        campground_id="cg_finger_lakes_001",
        name="Finger Lakes Test Campground",
        category="state_park",
        locality="Ithaca",
        region="NY",
        country_code="US",
        latitude=42.45,
        longitude=-76.52,
        amenities=CampgroundAmenitySummary(
            electric=True,
            water=True,
            dump_station=True,
            pet_friendly=True,
        ),
    ),
    CampgroundPublicRecord(
        campground_id="cg_central_pa_001",
        name="Central Pennsylvania Test Campground",
        category="public",
        locality="State College",
        region="PA",
        country_code="US",
        latitude=40.79,
        longitude=-77.86,
        amenities=CampgroundAmenitySummary(
            electric=True,
            water=True,
            sewer=True,
            wifi=True,
            showers=True,
            laundry=True,
            pet_friendly=True,
        ),
    ),
)


def _model_from_record(record: CampgroundPublicRecord) -> Campground:
    amenities = record.amenities
    return Campground(
        campground_id=record.campground_id,
        name=record.name,
        category=record.category,
        locality=record.locality,
        region=record.region,
        country_code=record.country_code,
        latitude=record.latitude,
        longitude=record.longitude,
        electric=amenities.electric,
        water=amenities.water,
        sewer=amenities.sewer,
        dump_station=amenities.dump_station,
        wifi=amenities.wifi,
        showers=amenities.showers,
        laundry=amenities.laundry,
        pet_friendly=amenities.pet_friendly,
        source=record.source,
        freshness=record.freshness,
    )


def _record_from_model(row: Campground) -> CampgroundPublicRecord:
    return CampgroundPublicRecord(
        campground_id=row.campground_id,
        name=row.name,
        category=row.category,  # type: ignore[arg-type]
        locality=row.locality,
        region=row.region,
        country_code=row.country_code,
        latitude=row.latitude,
        longitude=row.longitude,
        amenities=CampgroundAmenitySummary(
            electric=row.electric,
            water=row.water,
            sewer=row.sewer,
            dump_station=row.dump_station,
            wifi=row.wifi,
            showers=row.showers,
            laundry=row.laundry,
            pet_friendly=row.pet_friendly,
        ),
        source="deterministic_local",
        freshness="deterministic",
    )


def seed_deterministic_catalog(
    session: Session,
    records: Iterable[CampgroundPublicRecord] = DETERMINISTIC_CAMPGROUNDS,
) -> int:
    inserted = 0
    for record in records:
        if session.get(Campground, record.campground_id) is not None:
            continue
        session.add(_model_from_record(record))
        inserted += 1
    session.flush()
    return inserted


def _search_statement(query: CampgroundSearchQuery) -> Select[tuple[Campground]]:
    statement = select(Campground)
    if query.query:
        term = f"%{query.query.lower()}%"
        statement = statement.where(
            func.lower(Campground.name).like(term) | func.lower(Campground.locality).like(term)
        )
    if query.category:
        statement = statement.where(Campground.category == query.category)
    if query.region:
        statement = statement.where(Campground.region == query.region)
    if query.amenity:
        statement = statement.where(getattr(Campground, query.amenity).is_(True))
    return statement.order_by(Campground.name, Campground.campground_id).limit(query.limit)


def search_catalog(session: Session, query: CampgroundSearchQuery) -> list[CampgroundPublicRecord]:
    rows = session.scalars(_search_statement(query)).all()
    return [_record_from_model(row) for row in rows]
