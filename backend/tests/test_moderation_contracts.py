import uuid
from datetime import UTC, datetime
from typing import cast

import pytest
from pydantic import ValidationError

from app.moderation.contracts import (
    PROHIBITED_MODERATION_FIELDS,
    ReportCommand,
    ReportReason,
    ReportSummary,
    RestrictionCommand,
    RestrictionContext,
)


def test_report_command_is_closed_bounded_and_has_no_sensitive_evidence() -> None:
    command = ReportCommand(
        subject_account_id=uuid.uuid4(),
        reason="spam",
        idempotency_key="report-command-0001",
    )
    assert set(command.model_dump()) == {
        "subject_account_id",
        "reason",
        "idempotency_key",
    }

    for forbidden in sorted(PROHIBITED_MODERATION_FIELDS):
        with pytest.raises(ValidationError):
            ReportCommand.model_validate(
                {
                    **command.model_dump(),
                    forbidden: "attacker-controlled",
                }
            )


@pytest.mark.parametrize(
    "reason", ["harassment", "spam", "impersonation", "unsafe_content", "other"]
)
def test_report_reason_is_bounded(reason: str) -> None:
    command = ReportCommand(
        subject_account_id=uuid.uuid4(),
        reason=cast(ReportReason, reason),
        idempotency_key="report-command-0002",
    )
    assert command.reason == reason

    with pytest.raises(ValidationError):
        ReportCommand(
            subject_account_id=uuid.uuid4(),
            reason="custom-free-text",
            idempotency_key="report-command-0003",
        )


def test_report_summary_exposes_only_bounded_metadata() -> None:
    summary = ReportSummary(
        report_id=uuid.uuid4(),
        subject_account_id=uuid.uuid4(),
        reason="harassment",
        state="submitted",
        created_at=datetime.now(UTC),
    )
    assert set(summary.model_dump()) == {
        "report_id",
        "subject_account_id",
        "reason",
        "state",
        "created_at",
    }
    assert not PROHIBITED_MODERATION_FIELDS.intersection(summary.model_fields)


def test_restriction_context_is_restrictive_only() -> None:
    context = RestrictionContext(
        subject_account_id=uuid.uuid4(),
        kind="block",
        state="active",
    )
    assert context.restrictive_only is True
    assert context.authorization_source == "existing_roadtalk_authorization"

    with pytest.raises(ValidationError):
        RestrictionContext.model_validate(
            {**context.model_dump(), "restrictive_only": False}
        )
    with pytest.raises(ValidationError):
        RestrictionContext.model_validate(
            {**context.model_dump(), "authorization_source": "moderation"}
        )


def test_restriction_command_cannot_target_arbitrary_audiences() -> None:
    command = RestrictionCommand(subject_account_id=uuid.uuid4(), kind="mute")
    assert set(command.model_dump()) == {"subject_account_id", "kind"}

    for forbidden in (
        "recipient_ids",
        "nearby_users",
        "all_users",
        "latitude",
        "provider",
    ):
        with pytest.raises(ValidationError):
            RestrictionCommand.model_validate(
                {**command.model_dump(), forbidden: "override"}
            )


def test_report_idempotency_key_is_transport_safe() -> None:
    for invalid in (
        "contains spaces 0001",
        "contains/slash/0001",
        "contains\\nnewline0001",
    ):
        with pytest.raises(ValidationError):
            ReportCommand(
                subject_account_id=uuid.uuid4(),
                reason="spam",
                idempotency_key=invalid,
            )
