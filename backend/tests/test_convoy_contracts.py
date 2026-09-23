import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.convoys.contracts import (
    PROHIBITED_CONVOY_FIELDS,
    ConvoyJoinRequest,
    ConvoyLifecycleResponse,
    ConvoyMembershipContext,
    ConvoyMemberSummary,
    ConvoyPublicSummary,
)


def test_public_summary_is_closed_and_bounded() -> None:
    summary = ConvoyPublicSummary(
        convoy_id=uuid.uuid4(), display_name="Finger Lakes Caravan", state="active"
    )
    assert set(summary.model_dump()) == {"convoy_id", "display_name", "state"}

    for forbidden in sorted(PROHIBITED_CONVOY_FIELDS):
        with pytest.raises(ValidationError):
            ConvoyPublicSummary.model_validate(
                {
                    "convoy_id": uuid.uuid4(),
                    "display_name": "Test Convoy",
                    "state": "active",
                    forbidden: "attacker-controlled",
                }
            )


def test_member_summary_exposes_only_active_member_identity() -> None:
    member = ConvoyMemberSummary(account_id=uuid.uuid4(), callsign="RoadRunner", role="member")
    assert member.state == "active"
    assert set(member.model_dump()) == {"account_id", "callsign", "role", "state"}

    with pytest.raises(ValidationError):
        ConvoyMemberSummary(
            account_id=uuid.uuid4(), callsign="RoadRunner", role="member", state="revoked"
        )


def test_membership_context_cannot_claim_authorization() -> None:
    context = ConvoyMembershipContext(
        convoy_id=uuid.uuid4(), membership_id=uuid.uuid4(), role="leader", state="active"
    )
    assert context.context_only is True
    assert context.authorization_source == "existing_roadtalk_authorization"

    with pytest.raises(ValidationError):
        ConvoyMembershipContext.model_validate({**context.model_dump(), "context_only": False})
    with pytest.raises(ValidationError):
        ConvoyMembershipContext.model_validate(
            {**context.model_dump(), "authorization_source": "convoy_membership"}
        )


@pytest.mark.parametrize("state", ["left", "revoked", "expired", "disbanded"])
def test_non_active_lifecycle_states_are_explicit(state: str) -> None:
    response = ConvoyLifecycleResponse(
        convoy_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        state=state,
        changed_at=datetime.now(UTC),
    )
    assert response.state == state


def test_join_contract_accepts_only_opaque_invite() -> None:
    request = ConvoyJoinRequest(invite="x" * 40)
    assert set(request.model_dump()) == {"invite"}

    for forbidden in ("convoy_id", "account_id", "recipient_ids", "latitude", "provider"):
        with pytest.raises(ValidationError):
            ConvoyJoinRequest.model_validate({"invite": "x" * 40, forbidden: "override"})


def test_expiry_is_context_only_not_location_history() -> None:
    context = ConvoyMembershipContext(
        convoy_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        role="member",
        state="expired",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    assert context.state == "expired"
    assert not PROHIBITED_CONVOY_FIELDS.intersection(context.model_fields)
