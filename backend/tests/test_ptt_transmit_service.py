import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import MediaGrant
from app.ptt.provider import FakeMediaProvider
from app.ptt.service import (
    GrantError,
    create_transmit_grant,
    release_grant,
    release_transmit_grant,
)


def transmit_grant(*, now: datetime, revoked: bool = False) -> MediaGrant:
    receive_id = uuid.uuid4()
    return MediaGrant(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        parent_grant_id=receive_id,
        grant_kind="transmit",
        provider="livekit",
        provider_room_ref="room_opaque",
        provider_participant_ref="participant_opaque",
        action_scope="microphone_publish",
        policy_version="ptt-v1",
        idempotency_key_hash="a" * 64,
        request_fingerprint="b" * 64,
        issued_at=now,
        expires_at=now + timedelta(seconds=30),
        revoked_at=now if revoked else None,
        outcome_code="issued",
    )


def test_transmit_replay_returns_metadata_without_provider_call() -> None:
    async def exercise() -> None:
        now = datetime(2026, 7, 24, 12, tzinfo=UTC)
        grant = transmit_grant(now=now)
        account_id = grant.account_id
        device_id = grant.device_id
        receive_grant_id = grant.parent_grant_id
        assert receive_grant_id is not None
        key = "transmit-replay-key-0001"
        from app.ptt import service

        grant.idempotency_key_hash = service._digest(key)
        grant.request_fingerprint = service._transmit_fingerprint(receive_grant_id)
        db = AsyncMock(spec=AsyncSession)
        db.scalar.side_effect = [account_id, grant]
        provider = FakeMediaProvider(now=lambda: now)

        receipt = await create_transmit_grant(
            db,
            account_id=account_id,
            device_id=device_id,
            receive_grant_id=receive_grant_id,
            idempotency_key=key,
            settings=Settings(environment="test"),
            provider=provider,
            now=now,
        )
        assert receipt.grant_id == grant.id
        assert receipt.replayed is True
        assert provider.publish_requests == []

    asyncio.run(exercise())


def test_transmit_requires_active_owned_receive_grant() -> None:
    async def exercise() -> None:
        now = datetime(2026, 7, 24, 12, tzinfo=UTC)
        db = AsyncMock(spec=AsyncSession)
        db.scalar.side_effect = [uuid.uuid4(), None, None]
        with pytest.raises(GrantError) as denied:
            await create_transmit_grant(
                db,
                account_id=uuid.uuid4(),
                device_id=uuid.uuid4(),
                receive_grant_id=uuid.uuid4(),
                idempotency_key="transmit-invalid-key-0001",
                settings=Settings(environment="test"),
                provider=FakeMediaProvider(now=lambda: now),
                now=now,
            )
        assert denied.value.code == "PTT_RECEIVE_NOT_ACTIVE"

    asyncio.run(exercise())


def test_transmit_release_replay_and_unknown_grant_fail_closed() -> None:
    async def exercise() -> None:
        now = datetime(2026, 7, 24, 12, tzinfo=UTC)
        grant = transmit_grant(now=now, revoked=True)
        db = AsyncMock(spec=AsyncSession)
        db.scalar.return_value = grant
        receipt = await release_transmit_grant(
            db,
            account_id=grant.account_id,
            device_id=grant.device_id,
            grant_id=grant.id,
            provider=FakeMediaProvider(now=lambda: now),
            now=now,
        )
        assert receipt.replayed is True

        db.scalar.return_value = None
        with pytest.raises(GrantError) as missing:
            await release_grant(
                db,
                account_id=grant.account_id,
                device_id=grant.device_id,
                grant_id=uuid.uuid4(),
                provider=FakeMediaProvider(now=lambda: now),
                now=now,
            )
        assert missing.value.code == "PTT_GRANT_NOT_FOUND"

    asyncio.run(exercise())
