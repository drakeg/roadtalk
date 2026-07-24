import uuid
from datetime import datetime

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
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
    recovery_credential: Mapped["RecoveryCredential | None"] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )
    location_consent_events: Mapped[list["LocationConsentEvent"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    current_location: Mapped["CurrentLocation | None"] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )
    media_grants: Mapped[list["MediaGrant"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
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
    location_consent_events: Mapped[list["LocationConsentEvent"]] = relationship(
        back_populates="device", passive_deletes=True
    )
    current_locations: Mapped[list["CurrentLocation"]] = relationship(
        back_populates="source_device", passive_deletes=True
    )
    media_grants: Mapped[list["MediaGrant"]] = relationship(
        back_populates="device", passive_deletes=True
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


class RecoveryCredential(TimestampMixin, Base):
    __tablename__ = "recovery_credential"

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    key_id: Mapped[uuid.UUID] = mapped_column(unique=True)
    key_hash: Mapped[str] = mapped_column(String(255))
    rotated_at: Mapped[datetime]

    account: Mapped[Account] = relationship(back_populates="recovery_credential")


class LocationConsentEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "location_consent_event"
    __table_args__ = (
        CheckConstraint("decision IN ('granted', 'revoked')", name="decision_allowed"),
        CheckConstraint("platform IN ('android', 'ios')", name="platform_allowed"),
        CheckConstraint("length(policy_version) > 0", name="policy_version_present"),
        CheckConstraint("length(disclosure_version) > 0", name="disclosure_version_present"),
        Index("ix_location_consent_event_account_decided", "account_id", "decided_at"),
        Index("ix_location_consent_event_device_id", "device_id"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("device.id", ondelete="CASCADE"))
    policy_version: Mapped[str] = mapped_column(String(32))
    disclosure_version: Mapped[str] = mapped_column(String(32))
    platform: Mapped[str] = mapped_column(String(16))
    decision: Mapped[str] = mapped_column(String(16))
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped[Account] = relationship(back_populates="location_consent_events")
    device: Mapped[Device] = relationship(back_populates="location_consent_events")


class CurrentLocation(TimestampMixin, Base):
    __tablename__ = "current_location"
    __table_args__ = (
        CheckConstraint("horizontal_accuracy_m >= 0", name="accuracy_nonnegative"),
        CheckConstraint(
            "heading_deg IS NULL OR (heading_deg >= 0 AND heading_deg < 360)",
            name="heading_range",
        ),
        CheckConstraint("speed_mps IS NULL OR speed_mps >= 0", name="speed_nonnegative"),
        CheckConstraint("client_sequence >= 1", name="client_sequence_positive"),
        CheckConstraint("quality_state IN ('usable', 'degraded')", name="quality_state_allowed"),
        CheckConstraint("length(consent_policy_version) > 0", name="consent_policy_present"),
        CheckConstraint("expires_at > received_at", name="expiry_after_receipt"),
        CheckConstraint("version >= 1", name="version_positive"),
        Index("ix_current_location_position", "position", postgresql_using="gist"),
        Index("ix_current_location_source_device_id", "source_device_id"),
        Index("ix_current_location_expires_at", "expires_at"),
        Index("ix_current_location_effective", "quality_state", "expires_at"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    source_device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("device.id", ondelete="CASCADE"))
    position: Mapped[WKBElement] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    horizontal_accuracy_m: Mapped[float] = mapped_column(Float)
    heading_deg: Mapped[float | None] = mapped_column(Float)
    speed_mps: Mapped[float | None] = mapped_column(Float)
    client_sequence: Mapped[int] = mapped_column(BigInteger)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consent_policy_version: Mapped[str] = mapped_column(String(32))
    quality_state: Mapped[str] = mapped_column(String(16))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    account: Mapped[Account] = relationship(back_populates="current_location")
    source_device: Mapped[Device] = relationship(back_populates="current_locations")


class MediaGrant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "media_grant"
    __table_args__ = (
        CheckConstraint(
            "grant_kind IN ('receive', 'transmit')",
            name="grant_kind_allowed",
        ),
        CheckConstraint("provider = 'livekit'", name="provider_allowed"),
        CheckConstraint(
            "(grant_kind = 'receive' AND action_scope = 'subscribe') OR "
            "(grant_kind = 'transmit' AND action_scope = 'microphone_publish')",
            name="kind_scope_consistent",
        ),
        CheckConstraint(
            "(grant_kind = 'receive' AND parent_grant_id IS NULL) OR "
            "(grant_kind = 'transmit' AND parent_grant_id IS NOT NULL)",
            name="parent_consistent",
        ),
        CheckConstraint("length(provider_room_ref) > 0", name="room_ref_present"),
        CheckConstraint(
            "length(provider_participant_ref) > 0",
            name="participant_ref_present",
        ),
        CheckConstraint("length(policy_version) > 0", name="policy_version_present"),
        CheckConstraint("length(idempotency_key_hash) = 64", name="idempotency_hash_valid"),
        CheckConstraint("length(request_fingerprint) = 64", name="request_fingerprint_valid"),
        CheckConstraint("expires_at > issued_at", name="expiry_after_issue"),
        CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= issued_at",
            name="revocation_after_issue",
        ),
        Index(
            "ix_media_grant_account_kind_expires",
            "account_id",
            "grant_kind",
            "expires_at",
        ),
        Index("ix_media_grant_device_id", "device_id"),
        Index("ix_media_grant_parent_grant_id", "parent_grant_id"),
        Index(
            "uq_media_grant_account_kind_idempotency",
            "account_id",
            "grant_kind",
            "idempotency_key_hash",
            unique=True,
        ),
        Index(
            "ix_media_grant_provider_participant",
            "provider_room_ref",
            "provider_participant_ref",
        ),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("device.id", ondelete="CASCADE"))
    parent_grant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("media_grant.id", ondelete="CASCADE")
    )
    grant_kind: Mapped[str] = mapped_column(String(16))
    provider: Mapped[str] = mapped_column(String(16), default="livekit", server_default="livekit")
    provider_room_ref: Mapped[str] = mapped_column(String(128))
    provider_participant_ref: Mapped[str] = mapped_column(String(128))
    action_scope: Mapped[str] = mapped_column(String(32))
    policy_version: Mapped[str] = mapped_column(String(32))
    idempotency_key_hash: Mapped[str] = mapped_column(String(64))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome_code: Mapped[str | None] = mapped_column(String(64))

    account: Mapped[Account] = relationship(back_populates="media_grants")
    device: Mapped[Device] = relationship(back_populates="media_grants")
