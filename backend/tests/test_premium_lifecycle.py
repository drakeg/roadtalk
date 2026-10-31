import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.premium.lifecycle import (
    PremiumLifecycle,
    PremiumLifecycleError,
    PremiumLifecycleEvent,
)


def event(
    *,
    action: str,
    subscription_id: uuid.UUID,
    account_id: uuid.UUID,
    effective_at: datetime,
    expires_at: datetime | None = None,
    event_id: uuid.UUID | None = None,
) -> PremiumLifecycleEvent:
    return PremiumLifecycleEvent(
        event_id=event_id or uuid.uuid4(),
        subscription_id=subscription_id,
        account_id=account_id,
        action=action,
        effective_at=effective_at,
        expires_at=expires_at,
    )


def test_activation_and_renewal_are_server_authoritative() -> None:
    lifecycle = PremiumLifecycle()
    subscription_id = uuid.uuid4()
    account_id = uuid.uuid4()
    now = datetime.now(UTC)

    activated = lifecycle.apply(
        event(
            action="activate",
            subscription_id=subscription_id,
            account_id=account_id,
            effective_at=now,
            expires_at=now + timedelta(days=30),
        )
    )
    renewed = lifecycle.apply(
        event(
            action="renew",
            subscription_id=subscription_id,
            account_id=account_id,
            effective_at=now + timedelta(days=20),
            expires_at=now + timedelta(days=50),
        )
    )

    assert activated.subscription_state == "active"
    assert activated.entitlement_state == "active"
    assert renewed.subscription_state == "active"
    assert renewed.entitlement_state == "active"
    assert renewed.server_authoritative is True
    assert renewed.communication_authorization_unchanged is True


def test_cancel_keeps_entitlement_until_expiry_then_fails_closed() -> None:
    lifecycle = PremiumLifecycle()
    subscription_id = uuid.uuid4()
    account_id = uuid.uuid4()
    now = datetime.now(UTC)
    expiry = now + timedelta(days=30)

    lifecycle.apply(
        event(
            action="activate",
            subscription_id=subscription_id,
            account_id=account_id,
            effective_at=now,
            expires_at=expiry,
        )
    )
    canceled = lifecycle.apply(
        event(
            action="cancel",
            subscription_id=subscription_id,
            account_id=account_id,
            effective_at=now + timedelta(days=10),
        )
    )

    assert canceled.subscription_state == "canceled"
    assert canceled.entitlement_state == "active"

    current = lifecycle.current(subscription_id, observed_at=expiry)
    assert current is not None
    assert current.subscription_state == "expired"
    assert current.entitlement_state == "expired"


def test_revoke_removes_entitlement_immediately() -> None:
    lifecycle = PremiumLifecycle()
    subscription_id = uuid.uuid4()
    account_id = uuid.uuid4()
    now = datetime.now(UTC)

    lifecycle.apply(
        event(
            action="activate",
            subscription_id=subscription_id,
            account_id=account_id,
            effective_at=now,
            expires_at=now + timedelta(days=30),
        )
    )
    revoked = lifecycle.apply(
        event(
            action="revoke",
            subscription_id=subscription_id,
            account_id=account_id,
            effective_at=now + timedelta(days=1),
        )
    )

    assert revoked.subscription_state == "revoked"
    assert revoked.entitlement_state == "revoked"


def test_identical_event_replay_is_idempotent() -> None:
    lifecycle = PremiumLifecycle()
    subscription_id = uuid.uuid4()
    account_id = uuid.uuid4()
    now = datetime.now(UTC)
    activation = event(
        action="activate",
        subscription_id=subscription_id,
        account_id=account_id,
        effective_at=now,
        expires_at=now + timedelta(days=30),
    )

    first = lifecycle.apply(activation)
    replay = lifecycle.apply(activation)

    assert first.replayed is False
    assert replay.replayed is True
    assert replay.subscription_state == first.subscription_state
    assert replay.entitlement_state == first.entitlement_state


def test_conflicting_event_id_replay_fails_generically() -> None:
    lifecycle = PremiumLifecycle()
    subscription_id = uuid.uuid4()
    account_id = uuid.uuid4()
    event_id = uuid.uuid4()
    now = datetime.now(UTC)

    lifecycle.apply(
        event(
            action="activate",
            subscription_id=subscription_id,
            account_id=account_id,
            effective_at=now,
            expires_at=now + timedelta(days=30),
            event_id=event_id,
        )
    )

    with pytest.raises(PremiumLifecycleError, match="Premium lifecycle unavailable"):
        lifecycle.apply(
            event(
                action="activate",
                subscription_id=subscription_id,
                account_id=account_id,
                effective_at=now,
                expires_at=now + timedelta(days=60),
                event_id=event_id,
            )
        )


def test_stale_or_cross_account_transition_fails_closed() -> None:
    lifecycle = PremiumLifecycle()
    subscription_id = uuid.uuid4()
    account_id = uuid.uuid4()
    now = datetime.now(UTC)

    lifecycle.apply(
        event(
            action="activate",
            subscription_id=subscription_id,
            account_id=account_id,
            effective_at=now,
            expires_at=now + timedelta(days=30),
        )
    )

    with pytest.raises(PremiumLifecycleError, match="Premium lifecycle unavailable"):
        lifecycle.apply(
            event(
                action="renew",
                subscription_id=subscription_id,
                account_id=account_id,
                effective_at=now - timedelta(seconds=1),
                expires_at=now + timedelta(days=60),
            )
        )

    with pytest.raises(PremiumLifecycleError, match="Premium lifecycle unavailable"):
        lifecycle.apply(
            event(
                action="revoke",
                subscription_id=subscription_id,
                account_id=uuid.uuid4(),
                effective_at=now + timedelta(days=1),
            )
        )


def test_expire_cannot_run_before_the_authorized_expiry() -> None:
    lifecycle = PremiumLifecycle()
    subscription_id = uuid.uuid4()
    account_id = uuid.uuid4()
    now = datetime.now(UTC)
    expiry = now + timedelta(days=30)

    lifecycle.apply(
        event(
            action="activate",
            subscription_id=subscription_id,
            account_id=account_id,
            effective_at=now,
            expires_at=expiry,
        )
    )

    with pytest.raises(PremiumLifecycleError, match="Premium lifecycle unavailable"):
        lifecycle.apply(
            event(
                action="expire",
                subscription_id=subscription_id,
                account_id=account_id,
                effective_at=expiry - timedelta(seconds=1),
            )
        )

    expired = lifecycle.apply(
        event(
            action="expire",
            subscription_id=subscription_id,
            account_id=account_id,
            effective_at=expiry,
        )
    )
    assert expired.subscription_state == "expired"
    assert expired.entitlement_state == "expired"


def test_lifecycle_event_is_closed_and_requires_valid_expiry() -> None:
    now = datetime.now(UTC)
    subscription_id = uuid.uuid4()
    account_id = uuid.uuid4()

    with pytest.raises(ValidationError):
        PremiumLifecycleEvent(
            event_id=uuid.uuid4(),
            subscription_id=subscription_id,
            account_id=account_id,
            action="activate",
            effective_at=now,
        )

    valid = event(
        action="activate",
        subscription_id=subscription_id,
        account_id=account_id,
        effective_at=now,
        expires_at=now + timedelta(days=30),
    )
    with pytest.raises(ValidationError):
        PremiumLifecycleEvent.model_validate(
            {
                **valid.model_dump(),
                "payment_method_token": "attacker-controlled",
            }
        )


def test_concurrent_identical_event_is_applied_once_and_replayed_afterward() -> None:
    lifecycle = PremiumLifecycle()
    now = datetime.now(UTC)
    activation = event(
        action="activate",
        subscription_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        effective_at=now,
        expires_at=now + timedelta(days=30),
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        receipts = list(executor.map(lambda _: lifecycle.apply(activation), range(8)))

    assert sum(not receipt.replayed for receipt in receipts) == 1
    assert sum(receipt.replayed for receipt in receipts) == 7
    assert {receipt.subscription_state for receipt in receipts} == {"active"}
    assert {receipt.entitlement_state for receipt in receipts} == {"active"}
