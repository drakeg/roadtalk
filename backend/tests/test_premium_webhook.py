import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.premium.webhook import (
    MAX_PREMIUM_WEBHOOK_BYTES,
    PremiumWebhookBoundary,
    PremiumWebhookError,
)

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)
SECRET = b"roadtalk-local-test-webhook-secret-0001"


def boundary(**overrides: int) -> PremiumWebhookBoundary:
    return PremiumWebhookBoundary(secret=SECRET, **overrides)


def signed(
    value: PremiumWebhookBoundary,
    *,
    event_id: uuid.UUID,
    timestamp: datetime,
    body: bytes,
) -> str:
    return value.sign_for_test(event_id=event_id, timestamp=timestamp, body=body)


def test_valid_local_webhook_is_accepted_and_identical_replay_is_idempotent() -> None:
    value = boundary()
    event_id = uuid.uuid4()
    body = b'{"type":"subscription.updated"}'
    signature = signed(value, event_id=event_id, timestamp=NOW, body=body)

    first = value.verify(
        event_id=event_id,
        timestamp=NOW,
        body=body,
        signature=signature,
        now=NOW,
    )
    replay = value.verify(
        event_id=event_id,
        timestamp=NOW,
        body=body,
        signature=signature,
        now=NOW + timedelta(seconds=1),
    )

    assert first.replayed is False
    assert replay.replayed is True
    assert replay.event_id == event_id


def test_invalid_signature_stale_timestamp_and_oversize_payload_fail_closed() -> None:
    value = boundary()
    event_id = uuid.uuid4()
    body = b"{}"

    with pytest.raises(PremiumWebhookError, match="Premium webhook unavailable"):
        value.verify(
            event_id=event_id,
            timestamp=NOW,
            body=body,
            signature="0" * 64,
            now=NOW,
        )

    signature = signed(value, event_id=event_id, timestamp=NOW, body=body)
    with pytest.raises(PremiumWebhookError, match="Premium webhook unavailable"):
        value.verify(
            event_id=event_id,
            timestamp=NOW,
            body=body,
            signature=signature,
            now=NOW + timedelta(minutes=6),
        )

    huge = b"x" * (MAX_PREMIUM_WEBHOOK_BYTES + 1)
    with pytest.raises(PremiumWebhookError, match="Premium webhook unavailable"):
        value.verify(
            event_id=uuid.uuid4(),
            timestamp=NOW,
            body=huge,
            signature="0" * 64,
            now=NOW,
        )


def test_conflicting_event_reuse_fails_generically() -> None:
    value = boundary()
    event_id = uuid.uuid4()
    first = b'{"state":"active"}'
    second = b'{"state":"revoked"}'

    value.verify(
        event_id=event_id,
        timestamp=NOW,
        body=first,
        signature=signed(value, event_id=event_id, timestamp=NOW, body=first),
        now=NOW,
    )

    with pytest.raises(PremiumWebhookError, match="Premium webhook unavailable"):
        value.verify(
            event_id=event_id,
            timestamp=NOW,
            body=second,
            signature=signed(value, event_id=event_id, timestamp=NOW, body=second),
            now=NOW,
        )


def test_replay_storage_is_bounded_and_secrets_are_not_exposed() -> None:
    value = boundary(max_events=2)
    ids = [uuid.uuid4() for _ in range(3)]
    for event_id in ids:
        body = str(event_id).encode()
        value.verify(
            event_id=event_id,
            timestamp=NOW,
            body=body,
            signature=signed(value, event_id=event_id, timestamp=NOW, body=body),
            now=NOW,
        )

    assert len(value._seen) == 2
    assert ids[0] not in value._seen
    assert SECRET.decode() not in repr(value._seen)


def test_replay_still_requires_a_valid_signature() -> None:
    value = boundary()
    event_id = uuid.uuid4()
    body = b'{"state":"active"}'
    signature = signed(value, event_id=event_id, timestamp=NOW, body=body)
    value.verify(
        event_id=event_id,
        timestamp=NOW,
        body=body,
        signature=signature,
        now=NOW,
    )

    with pytest.raises(PremiumWebhookError, match="Premium webhook unavailable"):
        value.verify(
            event_id=event_id,
            timestamp=NOW,
            body=body,
            signature="0" * 64,
            now=NOW + timedelta(seconds=1),
        )
