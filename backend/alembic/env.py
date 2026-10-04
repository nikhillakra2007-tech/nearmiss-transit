"""Alembic env — imports Base metadata; URL from env DATABASE_URL."""
from __future__ import annotations
import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from backend.app.db.base import Base
from backend.app.db import models  # noqa

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://nearmiss:nearmiss@localhost:5432/nearmiss")
config.set_main_option("sqlalchemy.url", db_url)
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=db_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config({"sqlalchemy.url": db_url}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
