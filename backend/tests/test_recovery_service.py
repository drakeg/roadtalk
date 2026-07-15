import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.recovery.security import new_recovery_key
from app.recovery.service import RecoveryError, recover_account


def test_malformed_unknown_and_replayed_shapes_are_constant() -> None:
    settings = Settings(environment="test")
    malformed_db = AsyncMock()
    unknown_db = AsyncMock()
    unknown_db.scalar.return_value = None
    candidate = new_recovery_key().raw

    errors: list[RecoveryError] = []
    for database, raw_key in (
        (malformed_db, "malformed"),
        (unknown_db, candidate),
    ):
        with pytest.raises(RecoveryError) as raised:
            asyncio.run(
                recover_account(
                    database,
                    raw_key=raw_key,
                    installation_id=f"installation-{uuid.uuid4().hex}",
                    platform="ios",
                    settings=settings,
                )
            )
        errors.append(raised.value)

    assert [(error.code, error.detail) for error in errors] == [
        (
            "RECOVERY_FAILED",
            "The account could not be recovered with that key.",
        ),
        (
            "RECOVERY_FAILED",
            "The account could not be recovered with that key.",
        ),
    ]
    assert candidate not in str(errors[1])
    malformed_db.scalar.assert_not_awaited()
    unknown_db.scalar.assert_awaited_once()
