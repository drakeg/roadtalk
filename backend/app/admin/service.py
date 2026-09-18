import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.auth.service import AuthenticatedSession
from app.db.models import Account, AdminAuditEvent, Device, Profile, Session


class AdminAuthorizationError(ValueError):
    pass


class AdminMutationError(ValueError):
    pass


class AdminAccountSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: uuid.UUID
    status: str
    account_type: str
    callsign: str | None
    device_count: int = Field(ge=0)
    active_session_count: int = Field(ge=0)


class AdminAccountList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accounts: list[AdminAccountSummary]


class AdminMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: bool


class AdminMutationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: uuid.UUID
    status: str
    revoked_sessions: int = Field(default=0, ge=0)


def require_admin(current: AuthenticatedSession) -> None:
    if current.account.status != "active" or not current.account.is_admin:
        raise AdminAuthorizationError("Administrator authorization is required.")


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def list_accounts(
    db: AsyncSession, *, query: str | None = None, limit: int = 50
) -> AdminAccountList:
    statement = (
        select(Account)
        .options(selectinload(Account.profile))
        .order_by(Account.created_at.desc(), Account.id)
        .limit(limit)
    )
    normalized = (query or "").strip()
    if normalized:
        conditions: list[ColumnElement[bool]] = [Profile.display_callsign.ilike(f"%{normalized}%")]
        try:
            conditions.append(Account.id == uuid.UUID(normalized))
        except ValueError:
            pass
        statement = statement.outerjoin(Profile).where(or_(*conditions))
    accounts = list((await db.scalars(statement)).unique())
    rows: list[AdminAccountSummary] = []
    for account in accounts:
        device_count = await db.scalar(
            select(func.count()).select_from(Device).where(Device.account_id == account.id)
        )
        active_session_count = await db.scalar(
            select(func.count())
            .select_from(Session)
            .where(
                Session.account_id == account.id,
                Session.revoked_at.is_(None),
                Session.expires_at > _utcnow(),
            )
        )
        rows.append(
            AdminAccountSummary(
                account_id=account.id,
                status=account.status,
                account_type=account.account_type,
                callsign=account.profile.display_callsign if account.profile else None,
                device_count=device_count or 0,
                active_session_count=active_session_count or 0,
            )
        )
    return AdminAccountList(accounts=rows)


async def set_account_enabled(
    db: AsyncSession,
    *,
    actor: AuthenticatedSession,
    target_account_id: uuid.UUID,
    enabled: bool,
    confirmed: bool,
) -> AdminMutationResponse:
    if not confirmed:
        raise AdminMutationError("Explicit confirmation is required.")
    if actor.account.id == target_account_id and not enabled:
        raise AdminMutationError("Administrators cannot disable their current account.")
    target = await db.get(Account, target_account_id, with_for_update=True)
    if target is None or target.status == "deleted":
        raise AdminMutationError("Account is unavailable.")
    target.status = "active" if enabled else "disabled"
    revoked = 0
    if not enabled:
        active_session_ids = list(
            await db.scalars(
                select(Session.id).where(
                    Session.account_id == target.id, Session.revoked_at.is_(None)
                )
            )
        )
        await db.execute(
            update(Session)
            .where(Session.id.in_(active_session_ids))
            .values(revoked_at=_utcnow(), revoke_reason="admin_account_disabled")
        )
        revoked = len(active_session_ids)
    db.add(
        AdminAuditEvent(
            actor_account_id=actor.account.id,
            target_account_id=target.id,
            action="account_enabled" if enabled else "account_disabled",
        )
    )
    await db.commit()
    return AdminMutationResponse(
        account_id=target.id, status=target.status, revoked_sessions=revoked
    )


async def revoke_account_sessions(
    db: AsyncSession,
    *,
    actor: AuthenticatedSession,
    target_account_id: uuid.UUID,
    confirmed: bool,
) -> AdminMutationResponse:
    if not confirmed:
        raise AdminMutationError("Explicit confirmation is required.")
    target = await db.get(Account, target_account_id)
    if target is None or target.status == "deleted":
        raise AdminMutationError("Account is unavailable.")
    active_session_ids = list(
        await db.scalars(
            select(Session.id).where(Session.account_id == target.id, Session.revoked_at.is_(None))
        )
    )
    await db.execute(
        update(Session)
        .where(Session.id.in_(active_session_ids))
        .values(revoked_at=_utcnow(), revoke_reason="admin_revoked")
    )
    revoked = len(active_session_ids)
    db.add(
        AdminAuditEvent(
            actor_account_id=actor.account.id,
            target_account_id=target.id,
            action="sessions_revoked",
        )
    )
    await db.commit()
    return AdminMutationResponse(
        account_id=target.id, status=target.status, revoked_sessions=revoked
    )
