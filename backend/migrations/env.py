from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.db import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url.get_secret_value())
target_metadata = Base.metadata


def include_name(
    name: str | None,
    type_: Any,
    parent_names: Any,
) -> bool:
    if type_ == "schema":
        return name in {None, "public"}
    if type_ == "table":
        return parent_names.get("schema_name") in {None, "public"} and name != "spatial_ref_sys"
    return True


def include_object(
    object_: Any,
    name: str | None,
    type_: Any,
    reflected: bool,
    compare_to: Any,
) -> bool:
    del reflected, compare_to
    if type_ != "table":
        return True
    return getattr(object_, "schema", None) in {None, "public"} and name != "spatial_ref_sys"


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_schemas=True,
        include_name=include_name,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_schemas=True,
            include_name=include_name,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
