import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "account"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="status_allowed"),
        CheckConstraint("account_type IN ('anonymous', 'registered')", name="account_type_allowed"),
    )

    status: Mapped[str] = mapped_column(String(16), default="active", server_default="active")
    account_type: Mapped[str] = mapped_column(
        String(16), default="anonymous", server_default="anonymous"
    )
    deleted_at: Mapped[datetime | None]

    devices: Mapped[list["Device"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    profile: Mapped["Profile | None"] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )


class Device(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "device"
    __table_args__ = (
        CheckConstraint("platform IN ('android', 'ios')", name="platform_allowed"),
        Index("ix_device_account_id", "account_id"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))
    platform: Mapped[str] = mapped_column(String(16))
    installation_id: Mapped[str] = mapped_column(String(255), unique=True)
    push_token: Mapped[str | None] = mapped_column(Text)
    last_seen_at: Mapped[datetime | None]

    account: Mapped[Account] = relationship(back_populates="devices")
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )


class Session(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "session"
    __table_args__ = (
        Index("ix_session_account_id", "account_id"),
        Index("ix_session_device_id", "device_id"),
        Index("ix_session_refresh_family_id", "refresh_family_id"),
        Index("ix_session_expires_at", "expires_at"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("device.id", ondelete="CASCADE"))
    refresh_family_id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    revoke_reason: Mapped[str | None] = mapped_column(String(64))

    account: Mapped[Account] = relationship(back_populates="sessions")
    device: Mapped[Device] = relationship(back_populates="sessions")


class Profile(TimestampMixin, Base):
    __tablename__ = "profile"
    __table_args__ = (
        CheckConstraint(
            "(normalized_callsign IS NULL AND display_callsign IS NULL) OR "
            "(normalized_callsign IS NOT NULL AND display_callsign IS NOT NULL)",
            name="callsign_pair",
        ),
        CheckConstraint(
            "NOT setup_completed OR "
            "(normalized_callsign IS NOT NULL AND display_callsign IS NOT NULL "
            "AND avatar_id IS NOT NULL)",
            name="completed_fields",
        ),
        CheckConstraint("version >= 1", name="version_positive"),
        Index("uq_profile_normalized_callsign", "normalized_callsign", unique=True),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    normalized_callsign: Mapped[str | None] = mapped_column(String(32))
    display_callsign: Mapped[str | None] = mapped_column(String(32))
    avatar_id: Mapped[str | None] = mapped_column(String(64))
    setup_completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    callsign_changed_at: Mapped[datetime | None]

    account: Mapped[Account] = relationship(back_populates="profile")
