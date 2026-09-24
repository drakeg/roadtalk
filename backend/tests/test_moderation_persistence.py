import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import CheckConstraint, Table

from app.db import ModerationReport


def test_moderation_report_constraints_lock_bounded_lifecycle() -> None:
    names = {
        constraint.name
        for constraint in cast(Table, ModerationReport.__table__).constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert {
        "ck_moderation_report_reason_allowed",
        "ck_moderation_report_state_allowed",
        "ck_moderation_report_state_timestamp_consistent",
        "ck_moderation_report_different_accounts",
        "ck_moderation_report_idempotency_hash_valid",
        "ck_moderation_report_version_positive",
    } <= names


def test_moderation_report_stores_only_bounded_metadata() -> None:
    fields = {column.name for column in ModerationReport.__table__.columns}
    assert {
        "id",
        "reporter_account_id",
        "subject_account_id",
        "reason",
        "state",
        "idempotency_key_hash",
        "ended_at",
        "version",
        "created_at",
        "updated_at",
    } == fields
    assert not {
        "latitude",
        "longitude",
        "location",
        "route",
        "audio",
        "transcript",
        "attachment",
        "evidence",
        "free_text",
        "message",
        "notes",
        "provider_token",
    }.intersection(fields)


def test_moderation_report_idempotency_is_scoped_to_reporter() -> None:
    index = next(
        item
        for item in cast(Table, ModerationReport.__table__).indexes
        if item.name == "uq_moderation_report_reporter_idempotency"
    )
    assert index.unique is True
    assert [column.name for column in index.columns] == [
        "reporter_account_id",
        "idempotency_key_hash",
    ]


def test_terminal_report_has_end_timestamp_by_contract() -> None:
    report = ModerationReport(
        id=uuid.uuid4(),
        reporter_account_id=uuid.uuid4(),
        subject_account_id=uuid.uuid4(),
        reason="spam",
        state="withdrawn",
        idempotency_key_hash="a" * 64,
        ended_at=datetime.now(UTC),
    )
    assert report.state == "withdrawn"
    assert report.ended_at is not None


def test_report_relationships_are_directional() -> None:
    assert ModerationReport.reporter.property.back_populates == "submitted_reports"
    assert ModerationReport.subject.property.back_populates == "received_reports"
