import asyncio
import uuid
from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LocationConsentEvent
from app.location.consent import (
    LocationConsentError,
    LocationConsentReceipt,
    set_foreground_location_consent,
)


def session() -> tuple[AsyncSession, MagicMock]:
    raw = MagicMock()
    raw.scalar = AsyncMock(return_value=uuid.uuid4())
    raw.scalars = AsyncMock()
    raw.execute = AsyncMock()
    raw.commit = AsyncMock()
    return cast(AsyncSession, raw), raw


async def consent_call(db: AsyncSession, **overrides: object) -> LocationConsentReceipt:
    values: dict[str, object] = {
        "account_id": uuid.uuid4(),
        "device_id": uuid.uuid4(),
        "platform": "ios",
        "decision": "granted",
        "requested_policy_version": "location-v1",
        "requested_disclosure_version": "location-disclosure-v1",
        "current_policy_version": "location-v1",
        "current_disclosure_version": "location-disclosure-v1",
        "now": datetime(2026, 7, 15, 12, tzinfo=UTC),
    }
    values.update(overrides)
    return await set_foreground_location_consent(db, **values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"requested_policy_version": "old"}, "LOCATION_POLICY_MISMATCH"),
        ({"requested_disclosure_version": "old"}, "LOCATION_DISCLOSURE_MISMATCH"),
    ],
)
def test_consent_version_mismatch_fails_before_database_mutation(
    overrides: dict[str, object],
    code: str,
) -> None:
    async def scenario() -> None:
        db, raw = session()
        with pytest.raises(LocationConsentError) as raised:
            await consent_call(db, **overrides)
        assert raised.value.code == code
        raw.scalar.assert_not_awaited()
        raw.commit.assert_not_awaited()

    asyncio.run(scenario())


def test_matching_consent_replay_is_idempotent() -> None:
    async def scenario() -> None:
        now = datetime(2026, 7, 15, 12, tzinfo=UTC)
        event = LocationConsentEvent(
            account_id=uuid.uuid4(),
            device_id=uuid.uuid4(),
            policy_version="location-v1",
            disclosure_version="location-disclosure-v1",
            platform="ios",
            decision="granted",
            decided_at=now,
        )
        db, raw = session()
        result = MagicMock()
        result.first.return_value = event
        raw.scalars.return_value = result

        receipt = await consent_call(
            db,
            account_id=event.account_id,
            device_id=event.device_id,
            now=now,
        )

        assert receipt.decision == "granted"
        assert receipt.decided_at == now
        raw.add.assert_not_called()
        raw.execute.assert_not_awaited()
        raw.commit.assert_awaited_once()

    asyncio.run(scenario())


def test_revocation_appends_event_and_deletes_current_location_atomically() -> None:
    async def scenario() -> None:
        db, raw = session()
        result = MagicMock()
        result.first.return_value = None
        raw.scalars.return_value = result

        receipt = await consent_call(db, decision="revoked")

        assert receipt.decision == "revoked"
        raw.add.assert_called_once()
        raw.execute.assert_awaited_once()
        raw.commit.assert_awaited_once()

    asyncio.run(scenario())


def test_revocation_does_not_require_current_policy_acceptance() -> None:
    async def scenario() -> None:
        db, raw = session()
        result = MagicMock()
        result.first.return_value = None
        raw.scalars.return_value = result

        receipt = await consent_call(
            db,
            decision="revoked",
            requested_policy_version=None,
            requested_disclosure_version=None,
        )

        assert receipt.decision == "revoked"
        raw.commit.assert_awaited_once()

    asyncio.run(scenario())
