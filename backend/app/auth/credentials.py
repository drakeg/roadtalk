import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RegisteredCredential(TimestampMixin, Base):
    __tablename__ = "registered_credential"
    __table_args__ = (
        Index("uq_registered_credential_username", "normalized_username", unique=True),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    normalized_username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
