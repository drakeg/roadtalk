import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Account, AccountRouteMode


class RouteModeError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class RouteModeReceipt:
    mode: str
    version: int
    selected_at: datetime
    availability: str


def _receipt(selection: AccountRouteMode) -> RouteModeReceipt:
    return RouteModeReceipt(
        mode=selection.mode,
        version=selection.version,
        selected_at=selection.selected_at,
        availability="available" if selection.mode == "nearby" else "unavailable",
    )


async def _locked_selection(
    db: AsyncSession, *, account_id: uuid.UUID, now: datetime
) -> AccountRouteMode:
    account = await db.scalar(
        select(Account).where(Account.id == account_id).with_for_update()
    )
    if account is None or account.status != "active":
        raise RouteModeError("ROUTE_MODE_UNAVAILABLE", "The route mode is unavailable.")
    selection = await db.scalar(
        select(AccountRouteMode).where(AccountRouteMode.account_id == account_id).with_for_update()
    )
    if selection is None:
        selection = AccountRouteMode(
            account_id=account_id,
            mode="nearby",
            selected_at=now,
            version=1,
        )
        db.add(selection)
        await db.flush()
    return selection


async def get_route_mode(
    db: AsyncSession, *, account_id: uuid.UUID, now: datetime | None = None
) -> RouteModeReceipt:
    selection = await _locked_selection(
        db, account_id=account_id, now=now or datetime.now(UTC)
    )
    await db.commit()
    return _receipt(selection)


async def set_route_mode(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    mode: str,
    expected_version: int,
    now: datetime | None = None,
) -> RouteModeReceipt:
    resolved_now = now or datetime.now(UTC)
    selection = await _locked_selection(db, account_id=account_id, now=resolved_now)
    if expected_version == selection.version:
        if mode != selection.mode:
            selection.mode = mode
            selection.selected_at = resolved_now
            selection.version += 1
            await db.commit()
        else:
            await db.commit()
        return _receipt(selection)
    if expected_version + 1 == selection.version and mode == selection.mode:
        await db.commit()
        return _receipt(selection)
    await db.rollback()
    raise RouteModeError(
        "ROUTE_MODE_VERSION_CONFLICT",
        "The route mode changed; reload it before retrying.",
    )
