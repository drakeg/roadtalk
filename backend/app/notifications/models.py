import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class NotificationDeliveryReceipt(TimestampMixin, Base):
    """Bounded idempotency tombstone without audience or location history."""

    __tablename__ = "notification_delivery_receipt"
    __table_args__ = (
        CheckConstraint("length(idempotency_key_hash) = 64", name="idempotency_hash_valid"),
        CheckConstraint("length(request_fingerprint) = 64", name="request_fingerprint_valid"),
        Index("ix_notification_delivery_receipt_guard_expires", "guard_expires_at"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    idempotency_key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    notification_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("notification.id", ondelete="SET NULL"), nullable=True
    )
    guard_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
