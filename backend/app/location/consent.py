import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, cast

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Account, CurrentLocation, LocationConsentEvent


class LocationConsentError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class LocationConsentReceipt:
    decision: Literal["granted", "revoked"]
    policy_version: str
    disclosure_version: str
    decided_at: datetime


def _receipt(event: LocationConsentEvent) -> LocationConsentReceipt:
    return LocationConsentReceipt(
        decision=cast(Literal["granted", "revoked"], event.decision),
        policy_version=event.policy_version,
        disclosure_version=event.disclosure_version,
        decided_at=event.decided_at,
    )


async def set_foreground_location_consent(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    platform: str,
    decision: Literal["granted", "revoked"],
    requested_policy_version: str | None,
    requested_disclosure_version: str | None,
    current_policy_version: str,
    current_disclosure_version: str,
    now: datetime | None = None,
) -> LocationConsentReceipt:
    if decision == "granted" and requested_policy_version != current_policy_version:
        raise LocationConsentError(
            "LOCATION_POLICY_MISMATCH",
            "The foreground-location policy must be accepted again.",
        )
    if decision == "granted" and requested_disclosure_version != current_disclosure_version:
        raise LocationConsentError(
            "LOCATION_DISCLOSURE_MISMATCH",
            "The foreground-location disclosure must be accepted again.",
        )

    await db.scalar(select(Account.id).where(Account.id == account_id).with_for_update())
    current = (
        await db.scalars(
            select(LocationConsentEvent)
            .where(LocationConsentEvent.account_id == account_id)
            .order_by(
                LocationConsentEvent.decided_at.desc(),
                LocationConsentEvent.created_at.desc(),
                LocationConsentEvent.id.desc(),
            )
            .limit(1)
            .with_for_update()
        )
    ).first()
    if (
        current is not None
        and current.decision == decision
        and (
            decision == "revoked"
            or (
                current.policy_version == current_policy_version
                and current.disclosure_version == current_disclosure_version
            )
        )
    ):
        if decision == "revoked":
            await db.execute(
                delete(CurrentLocation).where(CurrentLocation.account_id == account_id)
            )
        await db.commit()
        return _receipt(current)

    event_policy_version = current_policy_version
    event_disclosure_version = current_disclosure_version
    if decision == "revoked" and current is not None:
        event_policy_version = current.policy_version
        event_disclosure_version = current.disclosure_version

    event = LocationConsentEvent(
        account_id=account_id,
        device_id=device_id,
        policy_version=event_policy_version,
        disclosure_version=event_disclosure_version,
        platform=platform,
        decision=decision,
        decided_at=(now or datetime.now(UTC)).astimezone(UTC),
    )
    db.add(event)
    if decision == "revoked":
        await db.execute(delete(CurrentLocation).where(CurrentLocation.account_id == account_id))
    await db.commit()
    return _receipt(event)
