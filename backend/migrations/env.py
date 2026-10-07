from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from devcom.bootstrap.settings import get_settings
from devcom.modules.billing.adapters import sqlalchemy_models as _billing_models  # noqa: F401
from devcom.modules.missions.adapters import sqlalchemy_models as _mission_models  # noqa: F401
from devcom.modules.missions.tech.adapters import sqlalchemy_models as _tech_models  # noqa: F401
from devcom.modules.projects.adapters import sqlalchemy_models as _project_models  # noqa: F401
from devcom.modules.projects.adapters import code_context_models as _code_ctx_models  # noqa: F401

from devcom.shared.persistence import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    settings = get_settings()
    settings.ensure_data_dir()
    return f"sqlite:///{settings.database_path}"


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
