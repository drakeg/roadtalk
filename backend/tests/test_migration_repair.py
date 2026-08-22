from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "migrations"
    / "versions"
    / "0011_repair_channel_idempotency.py"
)


def _load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0011", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Inspector:
    def __init__(self, *, columns: set[str], indexes: set[str]) -> None:
        self.columns = columns
        self.indexes = indexes

    def get_columns(self, table_name: str) -> list[dict[str, str]]:
        assert table_name == "channel"
        return [{"name": name} for name in self.columns]

    def get_indexes(self, table_name: str) -> list[dict[str, str]]:
        assert table_name == "channel"
        return [{"name": name} for name in self.indexes]


def test_repair_migration_adds_only_missing_channel_objects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migration = _load_migration()
    inspector = _Inspector(columns={"id", "creator_account_id"}, indexes=set())
    added_columns: list[str] = []
    added_indexes: list[tuple[str, tuple[str, ...], bool]] = []

    monkeypatch.setattr(migration.sa, "inspect", lambda bind: inspector)
    monkeypatch.setattr(migration.op, "get_bind", lambda: object())
    monkeypatch.setattr(
        migration.op,
        "add_column",
        lambda table, column: added_columns.append(f"{table}.{column.name}"),
    )

    def create_index(
        name: str,
        table: str,
        columns: list[str],
        *,
        unique: bool,
        **kwargs: Any,
    ) -> None:
        del table, kwargs
        added_indexes.append((name, tuple(columns), unique))

    monkeypatch.setattr(migration.op, "create_index", create_index)

    migration.upgrade()

    assert added_columns == [
        "channel.create_idempotency_hash",
        "channel.create_request_fingerprint",
    ]
    assert added_indexes == [
        (
            "uq_channel_creator_create_idempotency",
            ("creator_account_id", "create_idempotency_hash"),
            True,
        )
    ]


def test_repair_migration_leaves_canonical_schema_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migration = _load_migration()
    inspector = _Inspector(
        columns={
            "id",
            "creator_account_id",
            "create_idempotency_hash",
            "create_request_fingerprint",
        },
        indexes={"uq_channel_creator_create_idempotency"},
    )

    monkeypatch.setattr(migration.sa, "inspect", lambda bind: inspector)
    monkeypatch.setattr(migration.op, "get_bind", lambda: object())
    monkeypatch.setattr(
        migration.op,
        "add_column",
        lambda *args, **kwargs: pytest.fail(f"unexpected add_column: {args}, {kwargs}"),
    )
    monkeypatch.setattr(
        migration.op,
        "create_index",
        lambda *args, **kwargs: pytest.fail(f"unexpected create_index: {args}, {kwargs}"),
    )

    migration.upgrade()
