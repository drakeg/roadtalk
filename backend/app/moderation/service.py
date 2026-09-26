import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Account, ModerationReport, ModerationRestriction
from app.moderation.contracts import ReportReason


class ReportLifecycleError(ValueError):
    pass


def _idempotency_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


async def submit_report(
    db: AsyncSession,
    *,
    reporter: Account,
    subject_account_id: uuid.UUID,
    reason: ReportReason,
    idempotency_key: str,
) -> ModerationReport:
    if reporter.status != "active" or reporter.id == subject_account_id:
        raise ReportLifecycleError("report unavailable")

    subject = await db.get(Account, subject_account_id)
    if subject is None or subject.status == "deleted":
        raise ReportLifecycleError("report unavailable")

    key_hash = _idempotency_hash(idempotency_key)
    existing = await db.scalar(
        select(ModerationReport).where(
            ModerationReport.reporter_account_id == reporter.id,
            ModerationReport.idempotency_key_hash == key_hash,
        )
    )
    if existing is not None:
        if existing.subject_account_id == subject_account_id and existing.reason == reason:
            return existing
        raise ReportLifecycleError("report unavailable")

    report = ModerationReport(
        reporter_account_id=reporter.id,
        subject_account_id=subject_account_id,
        reason=reason,
        state="submitted",
        idempotency_key_hash=key_hash,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def end_report(
    db: AsyncSession,
    *,
    report_id: uuid.UUID,
    reporter_account_id: uuid.UUID,
    state: str,
) -> ModerationReport:
    if state not in {"closed", "withdrawn"}:
        raise ReportLifecycleError("report unavailable")

    report = await db.get(ModerationReport, report_id, with_for_update=True)
    if (
        report is None
        or report.reporter_account_id != reporter_account_id
        or report.state != "submitted"
    ):
        raise ReportLifecycleError("report unavailable")

    report.state = state
    report.ended_at = datetime.now(UTC)
    report.version += 1
    await db.commit()
    await db.refresh(report)
    return report


class RestrictionLifecycleError(ValueError):
    pass


async def set_restriction(
    db: AsyncSession,
    *,
    actor: Account,
    subject_account_id: uuid.UUID,
    kind: str,
) -> ModerationRestriction:
    if kind not in {"mute", "block"} or actor.status != "active" or actor.id == subject_account_id:
        raise RestrictionLifecycleError("moderation unavailable")
    subject = await db.get(Account, subject_account_id)
    if subject is None or subject.status == "deleted":
        raise RestrictionLifecycleError("moderation unavailable")
    existing = await db.scalar(
        select(ModerationRestriction).where(
            ModerationRestriction.actor_account_id == actor.id,
            ModerationRestriction.subject_account_id == subject_account_id,
            ModerationRestriction.kind == kind,
            ModerationRestriction.state == "active",
        )
    )
    if existing is not None:
        return existing
    restriction = ModerationRestriction(
        actor_account_id=actor.id,
        subject_account_id=subject_account_id,
        kind=kind,
        state="active",
    )
    db.add(restriction)
    await db.commit()
    await db.refresh(restriction)
    return restriction


async def revoke_restriction(
    db: AsyncSession,
    *,
    actor_account_id: uuid.UUID,
    restriction_id: uuid.UUID,
) -> ModerationRestriction:
    restriction = await db.get(ModerationRestriction, restriction_id, with_for_update=True)
    if (
        restriction is None
        or restriction.actor_account_id != actor_account_id
        or restriction.state != "active"
    ):
        raise RestrictionLifecycleError("moderation unavailable")
    restriction.state = "revoked"
    restriction.ended_at = datetime.now(UTC)
    restriction.version += 1
    await db.commit()
    await db.refresh(restriction)
    return restriction
