import asyncio
import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from math import ceil
from time import perf_counter

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, Device
from app.ptt.provider import FakeMediaProvider
from app.ptt.service import GrantError, create_receive_grant, create_transmit_grant


def _p95(milliseconds: list[float]) -> float:
    ordered = sorted(milliseconds)
    return ordered[max(0, ceil(len(ordered) * 0.95) - 1)]


def _fixed_ref(value: str) -> Callable[[], str]:
    return lambda: value


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_grant_service_at_synthetic_field_test_scale() -> None:
    asyncio.run(_grant_service_at_synthetic_field_test_scale())


async def _grant_service_at_synthetic_field_test_scale() -> None:
    """Measure grant latency with 100 accounts, 25 receivers, and 10 publishers."""
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime(2026, 8, 4, 3, tzinfo=UTC)
    provider = FakeMediaProvider(now=lambda: now)
    accounts = [Account() for _ in range(100)]
    devices = [
        Device(
            account=account,
            platform="ios" if index % 2 == 0 else "android",
            installation_id=f"ptt-scale-{index:03d}-{datetime.now(UTC).timestamp()}",
        )
        for index, account in enumerate(accounts)
    ]
    eligible_ms: list[float] = []
    denied_ms: list[float] = []

    try:
        async with factory() as db:
            db.add_all(accounts)
            await db.commit()

            receive_grants = []
            for index in range(25):
                started = perf_counter()
                receive_grant = await create_receive_grant(
                    db,
                    account_id=accounts[index].id,
                    device_id=devices[index].id,
                    idempotency_key=f"scale-receive-{index:03d}",
                    settings=settings,
                    provider=provider,
                    now=now,
                    random_ref=_fixed_ref(f"scale{index:03d}"),
                )
                eligible_ms.append((perf_counter() - started) * 1_000)
                receive_grants.append(receive_grant)

            transmit_grants = []
            for index in range(10):
                started = perf_counter()
                transmit_grant = await create_transmit_grant(
                    db,
                    account_id=accounts[index].id,
                    device_id=devices[index].id,
                    receive_grant_id=receive_grants[index].grant_id,
                    idempotency_key=f"scale-transmit-{index:03d}",
                    settings=settings,
                    provider=provider,
                    now=now,
                )
                eligible_ms.append((perf_counter() - started) * 1_000)
                transmit_grants.append(transmit_grant)

            # Idempotent replays add authenticated eligible load without increasing
            # provider connections or publisher state beyond the approved scale.
            for _ in range(2):
                for index in range(25):
                    started = perf_counter()
                    await create_receive_grant(
                        db,
                        account_id=accounts[index].id,
                        device_id=devices[index].id,
                        idempotency_key=f"scale-receive-{index:03d}",
                        settings=settings,
                        provider=provider,
                        now=now,
                    )
                    eligible_ms.append((perf_counter() - started) * 1_000)

            for index in range(10):
                started = perf_counter()
                replay = await create_transmit_grant(
                    db,
                    account_id=accounts[index].id,
                    device_id=devices[index].id,
                    receive_grant_id=receive_grants[index].grant_id,
                    idempotency_key=f"scale-transmit-{index:03d}",
                    settings=settings,
                    provider=provider,
                    now=now,
                )
                eligible_ms.append((perf_counter() - started) * 1_000)
                assert replay.grant_id == transmit_grants[index].grant_id

            for index in range(10):
                started = perf_counter()
                with pytest.raises(GrantError) as denied:
                    await create_transmit_grant(
                        db,
                        account_id=accounts[index].id,
                        device_id=devices[index].id,
                        receive_grant_id=receive_grants[index].grant_id,
                        idempotency_key=f"scale-busy-{index:03d}",
                        settings=settings,
                        provider=provider,
                        now=now,
                    )
                denied_ms.append((perf_counter() - started) * 1_000)
                assert denied.value.code == "PTT_TRANSMIT_BUSY"

            eligible_p95_ms = _p95(eligible_ms)
            denied_p95_ms = _p95(denied_ms)
            print(
                "PTT synthetic scale: "
                + json.dumps(
                    {
                        "registered_accounts": 100,
                        "connected_receivers": 25,
                        "active_publishers": 10,
                        "eligible_requests": len(eligible_ms),
                        "denied_requests": len(denied_ms),
                        "eligible_p95_ms": round(eligible_p95_ms, 2),
                        "denied_p95_ms": round(denied_p95_ms, 2),
                        "target_ms": 250,
                    },
                    sort_keys=True,
                )
            )
            assert eligible_p95_ms <= 250
            assert denied_p95_ms <= 250

            await db.execute(delete(Account).where(Account.id.in_([a.id for a in accounts])))
            await db.commit()
    finally:
        await engine.dispose()
