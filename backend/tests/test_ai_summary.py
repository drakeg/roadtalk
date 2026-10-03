import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.ai.provider import AiProviderBoundary, DisabledAiProvider, FakeAiProvider
from app.ai.summary import (
    SUMMARY_RESULT_MAX_CHARS,
    SUMMARY_SOURCE_MAX_CHARS,
    AuthorizedSummarySource,
    SummaryError,
    summarize_authorized_text,
)


def source(now: datetime) -> AuthorizedSummarySource:
    return AuthorizedSummarySource(
        source_id=uuid.uuid4(),
        source_kind="transcript",
        text="Authorized conversation text.",
        language="en",
        observed_at=now,
        expires_at=now + timedelta(minutes=5),
    )


def test_summary_preserves_source_provenance_and_authorization() -> None:
    now = datetime(2026, 10, 3, 13, 0, tzinfo=UTC)
    value = source(now)
    request_id = uuid.uuid4()
    receipt = asyncio.run(
        summarize_authorized_text(
            source=value,
            provider=AiProviderBoundary(
                FakeAiProvider(outputs={request_id: "Bounded deterministic summary."})
            ),
            now=now + timedelta(seconds=1),
            request_id=request_id,
        )
    )

    assert receipt.request_id == request_id
    assert receipt.source_id == value.source_id
    assert receipt.source_kind == "transcript"
    assert receipt.summary == "Bounded deterministic summary."
    assert receipt.source_language == "en"
    assert receipt.state == "ready"
    assert receipt.provider_mode == "test"
    assert receipt.source_expires_at == value.expires_at
    assert receipt.authorization_source == "existing_roadtalk_authorization"


def test_stale_source_fails_closed_before_provider_call() -> None:
    now = datetime(2026, 10, 3, 13, 0, tzinfo=UTC)
    value = AuthorizedSummarySource(
        source_id=uuid.uuid4(),
        source_kind="message_window",
        text="Authorized but expired text.",
        language="en",
        observed_at=now - timedelta(minutes=10),
        expires_at=now - timedelta(seconds=1),
    )
    provider = FakeAiProvider()

    with pytest.raises(SummaryError) as error:
        asyncio.run(
            summarize_authorized_text(
                source=value,
                provider=AiProviderBoundary(provider),
                now=now,
            )
        )

    assert error.value.code == "AI_SUMMARY_SOURCE_STALE"
    assert provider.text_requests == []


def test_disabled_provider_is_normalized_to_generic_unavailable_error() -> None:
    now = datetime(2026, 10, 3, 13, 0, tzinfo=UTC)
    with pytest.raises(SummaryError) as error:
        asyncio.run(
            summarize_authorized_text(
                source=source(now),
                provider=AiProviderBoundary(DisabledAiProvider()),
                now=now,
            )
        )
    assert error.value.code == "AI_SUMMARY_UNAVAILABLE"
    assert "provider" not in error.value.detail.lower()


def test_summary_source_is_closed_and_sensitive_overposting_is_rejected() -> None:
    now = datetime(2026, 10, 3, 13, 0, tzinfo=UTC)
    value = source(now)

    for field in (
        "latitude",
        "longitude",
        "route_history",
        "audio",
        "recipient_ids",
        "nearby_users",
        "provider_key",
        "model",
        "prompt",
    ):
        with pytest.raises(ValidationError):
            AuthorizedSummarySource.model_validate(
                {**value.model_dump(), field: "attacker-controlled"}
            )


def test_summary_source_and_result_bounds_are_enforced() -> None:
    now = datetime(2026, 10, 3, 13, 0, tzinfo=UTC)

    with pytest.raises(ValidationError):
        AuthorizedSummarySource(
            source_id=uuid.uuid4(),
            source_kind="transcript",
            text="x" * (SUMMARY_SOURCE_MAX_CHARS + 1),
            language="en",
            observed_at=now,
            expires_at=now + timedelta(minutes=1),
        )

    with pytest.raises(SummaryError) as error:
        asyncio.run(
            summarize_authorized_text(
                source=source(now),
                provider=AiProviderBoundary(FakeAiProvider()),
                max_output_chars=SUMMARY_RESULT_MAX_CHARS + 1,
                now=now,
            )
        )
    assert error.value.code == "AI_SUMMARY_BOUNDS_INVALID"


def test_provider_output_larger_than_requested_bound_is_rejected() -> None:
    now = datetime(2026, 10, 3, 13, 0, tzinfo=UTC)
    request_id = uuid.uuid4()

    with pytest.raises(SummaryError) as error:
        asyncio.run(
            summarize_authorized_text(
                source=source(now),
                provider=AiProviderBoundary(FakeAiProvider(outputs={request_id: "x" * 101})),
                max_output_chars=100,
                now=now,
                request_id=request_id,
            )
        )

    assert error.value.code == "AI_SUMMARY_OUTPUT_INVALID"


def test_source_timestamps_must_be_aware_and_expiry_must_follow_observation() -> None:
    naive = datetime(2026, 10, 3, 13, 0)
    with pytest.raises(ValidationError):
        AuthorizedSummarySource(
            source_id=uuid.uuid4(),
            source_kind="transcript",
            text="Authorized text.",
            language="en",
            observed_at=naive,
            expires_at=naive + timedelta(minutes=1),
        )

    now = datetime(2026, 10, 3, 13, 0, tzinfo=UTC)
    with pytest.raises(ValidationError):
        AuthorizedSummarySource(
            source_id=uuid.uuid4(),
            source_kind="transcript",
            text="Authorized text.",
            language="en",
            observed_at=now,
            expires_at=now,
        )
