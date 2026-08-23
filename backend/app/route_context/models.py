import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CurrentRouteContext(TimestampMixin, Base):
    __tablename__ = "current_route_context"
    __table_args__ = (
        CheckConstraint("length(corridor_digest) = 64", name="corridor_digest_length"),
        CheckConstraint(
            "direction IN ('north', 'northeast', 'east', 'southeast', 'south', "
            "'southwest', 'west', 'northwest', 'stationary', 'unknown')",
            name="direction_allowed",
        ),
        CheckConstraint("confidence = 'confident'", name="confidence_confident_only"),
        CheckConstraint("source_location_version >= 1", name="source_location_version_positive"),
        CheckConstraint("length(provider_version) > 0", name="provider_version_present"),
        CheckConstraint("length(policy_version) > 0", name="policy_version_present"),
        CheckConstraint("expires_at > matched_at", name="expiry_after_match"),
        CheckConstraint("version >= 1", name="version_positive"),
        Index("ix_current_route_context_expires_at", "expires_at"),
        Index(
            "ix_current_route_context_corridor_direction",
            "corridor_digest",
            "direction",
            "expires_at",
        ),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("current_location.account_id", ondelete="CASCADE"), primary_key=True
    )
    corridor_digest: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[str] = mapped_column(String(16))
    source_location_version: Mapped[int] = mapped_column(Integer)
    provider_version: Mapped[str] = mapped_column(String(32))
    policy_version: Mapped[str] = mapped_column(String(32))
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
