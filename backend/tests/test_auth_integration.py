import asyncio
import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.schemas import AnonymousSessionRequest
from app.auth.service import (
    AuthenticationError,
    authenticate_session,
    create_anonymous_session,
    revoke_device_sessions,
    rotate_refresh_token,
)
from app.channels.constants import GENERAL_CHANNEL_ID
from app.config import Settings
from app.db.models import ChannelSelection, MediaGrant


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_anonymous_session_rotation_replay_and_device_revocation() -> None:
    asyncio.run(_lifecycle())


async def _lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    installation_id = "integration-" + os.urandom(16).hex()

    try:
        async with factory() as db:
            created = await create_anonymous_session(
                db,
                AnonymousSessionRequest(
                    installation_id=installation_id,
                    platform="ios",
                ),
                settings,
            )
            identity = await authenticate_session(
                db,
                account_id=created.account_id,
                device_id=created.device_id,
                session_id=created.session_id,
            )
            assert identity.account.account_type == "anonymous"
            selection = await db.get(ChannelSelection, created.account_id)
            assert selection is not None
            assert selection.channel_id == GENERAL_CHANNEL_ID
            assert selection.version == 1

            issued_at = datetime.now(UTC)
            session_grant = MediaGrant(
                account_id=created.account_id,
                device_id=created.device_id,
                parent_grant_id=None,
                grant_kind="receive",
                provider="livekit",
                provider_room_ref="room_auth_integration",
                provider_participant_ref="participant_session_revoke",
                action_scope="subscribe",
                policy_version="ptt-v1",
                idempotency_key_hash="a" * 64,
                request_fingerprint="b" * 64,
                issued_at=issued_at,
                expires_at=issued_at + timedelta(minutes=5),
                revoked_at=None,
                outcome_code="issued",
            )
            db.add(session_grant)
            await db.commit()

            replacement = await rotate_refresh_token(db, created.refresh_token, settings)
            with pytest.raises(AuthenticationError) as replay:
                await rotate_refresh_token(db, created.refresh_token, settings)
            assert replay.value.code == "REFRESH_REPLAY_DETECTED"
            await db.refresh(session_grant)
            assert session_grant.revoked_at is not None
            assert session_grant.outcome_code == "session_revoked"

            with pytest.raises(AuthenticationError) as family_revoked:
                await rotate_refresh_token(db, replacement.refresh_token, settings)
            assert family_revoked.value.code == "REFRESH_REPLAY_DETECTED"

            device_grant = MediaGrant(
                account_id=created.account_id,
                device_id=created.device_id,
                parent_grant_id=None,
                grant_kind="receive",
                provider="livekit",
                provider_room_ref="room_auth_integration",
                provider_participant_ref="participant_device_revoke",
                action_scope="subscribe",
                policy_version="ptt-v1",
                idempotency_key_hash="c" * 64,
                request_fingerprint="d" * 64,
                issued_at=issued_at,
                expires_at=issued_at + timedelta(minutes=5),
                revoked_at=None,
                outcome_code="issued",
            )
            db.add(device_grant)
            await db.commit()

            count = await revoke_device_sessions(
                db,
                account_id=created.account_id,
                device_id=created.device_id,
            )
            assert count == 0
            await db.refresh(device_grant)
            assert device_grant.revoked_at is not None
            assert device_grant.outcome_code == "device_revoked"
            await db.delete(identity.account)
            await db.commit()
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(MediaGrant)
                    .where(MediaGrant.account_id == created.account_id)
                )
                == 0
            )
    finally:
        await engine.dispose()
