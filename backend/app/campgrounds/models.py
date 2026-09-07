from sqlalchemy import Boolean, CheckConstraint, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Campground(TimestampMixin, Base):
    __tablename__ = "campground"
    __table_args__ = (
        CheckConstraint(
            "category IN ('public', 'private', 'state_park', 'national_park', "
            "'county_municipal', 'other')",
            name="ck_campground_category_allowed",
        ),
        CheckConstraint(
            "length(country_code) = 2 AND upper(country_code) = country_code",
            name="ck_campground_country_code",
        ),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_campground_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_campground_longitude"),
        CheckConstraint("source = 'deterministic_local'", name="ck_campground_source"),
        CheckConstraint("freshness = 'deterministic'", name="ck_campground_freshness"),
        Index("ix_campground_region_category", "region", "category"),
        Index("ix_campground_name", "name"),
    )

    campground_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(32))
    locality: Mapped[str] = mapped_column(String(96))
    region: Mapped[str] = mapped_column(String(64))
    country_code: Mapped[str] = mapped_column(String(2))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    electric: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    water: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sewer: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    dump_station: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    wifi: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    showers: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    laundry: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    pet_friendly: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    source: Mapped[str] = mapped_column(
        String(32), default="deterministic_local", server_default="deterministic_local"
    )
    freshness: Mapped[str] = mapped_column(
        String(32), default="deterministic", server_default="deterministic"
    )
