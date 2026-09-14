import uuid
from datetime import UTC, datetime, timedelta

from app.campgrounds.communication import compose_campground_communication
from app.campgrounds.context import CurrentCampgroundContext
from app.campgrounds.contracts import CampgroundContextLabel
from app.ptt.proximity import EligibleReceiveGrant


def _grant(account_id: uuid.UUID) -> EligibleReceiveGrant:
    return EligibleReceiveGrant(
        receive_grant_id=uuid.uuid4(),
        account_id=account_id,
        device_id=uuid.uuid4(),
        participant_ref=f"participant-{account_id}",
    )


def _context(campground_id: str, *, expires_at: datetime) -> CurrentCampgroundContext:
    return CurrentCampgroundContext(
        label=CampgroundContextLabel(
            campground_id=campground_id,
            name=f"{campground_id} Test Campground",
            state="current",
        ),
        expires_at=expires_at,
    )


def test_campground_composition_only_narrows_upstream_authorization() -> None:
    now = datetime.now(UTC)
    first_account = uuid.uuid4()
    second_account = uuid.uuid4()
    third_account = uuid.uuid4()
    upstream = tuple(_grant(account_id) for account_id in (first_account, second_account))

    composition = compose_campground_communication(
        sender_context=_context("cg_test_001", expires_at=now + timedelta(minutes=5)),
        already_authorized_receivers=upstream,
        receiver_contexts={
            first_account: _context("cg_test_001", expires_at=now + timedelta(minutes=5)),
            second_account: _context("cg_test_002", expires_at=now + timedelta(minutes=5)),
            third_account: _context("cg_test_001", expires_at=now + timedelta(minutes=5)),
        },
        now=now,
    )

    assert composition is not None
    assert composition.eligible_receivers == (upstream[0],)
    assert third_account not in {item.account_id for item in composition.eligible_receivers}


def test_missing_or_expired_sender_context_fails_closed() -> None:
    now = datetime.now(UTC)
    account_id = uuid.uuid4()
    upstream = (_grant(account_id),)

    assert (
        compose_campground_communication(
            sender_context=None,
            already_authorized_receivers=upstream,
            receiver_contexts={},
            now=now,
        )
        is None
    )
    assert (
        compose_campground_communication(
            sender_context=_context("cg_test_001", expires_at=now),
            already_authorized_receivers=upstream,
            receiver_contexts={account_id: _context("cg_test_001", expires_at=now)},
            now=now,
        )
        is None
    )


def test_receiver_context_must_be_current_and_same_campground() -> None:
    now = datetime.now(UTC)
    current_account = uuid.uuid4()
    stale_account = uuid.uuid4()
    other_account = uuid.uuid4()
    upstream = (
        _grant(current_account),
        _grant(stale_account),
        _grant(other_account),
    )

    composition = compose_campground_communication(
        sender_context=_context("cg_test_001", expires_at=now + timedelta(minutes=5)),
        already_authorized_receivers=upstream,
        receiver_contexts={
            current_account: _context("cg_test_001", expires_at=now + timedelta(minutes=5)),
            stale_account: _context("cg_test_001", expires_at=now),
            other_account: _context("cg_test_002", expires_at=now + timedelta(minutes=5)),
        },
        now=now,
    )

    assert composition is not None
    assert tuple(item.account_id for item in composition.eligible_receivers) == (current_account,)


def test_public_context_exposes_no_membership_or_occupancy() -> None:
    now = datetime.now(UTC)
    composition = compose_campground_communication(
        sender_context=_context("cg_test_001", expires_at=now + timedelta(minutes=5)),
        already_authorized_receivers=(),
        receiver_contexts={},
        now=now,
    )

    assert composition is not None
    assert composition.context.model_dump() == {
        "campground_id": "cg_test_001",
        "context_only": True,
        "authorization_source": "existing_roadtalk_authorization",
    }
    serialized = composition.context.model_dump()
    assert "members" not in serialized
    assert "member_ids" not in serialized
    assert "occupancy" not in serialized
    assert "recipient_ids" not in serialized
