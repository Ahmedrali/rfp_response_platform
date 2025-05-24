import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool, create_engine # Ensure create_engine is imported
from sqlalchemy.engine import Connection
# from sqlalchemy.ext.asyncio import create_async_engine # Not used for Alembic's core sync operations

from alembic import context

# Import our models for autogenerate support
from app.models import Base
from app.utils.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Process the DB URL - convert from asyncpg format to psycopg2 for Alembic
# and remove any schema query parameter if present.
# Also, prepare connect_args for the synchronous engine.
raw_db_url = settings.DATABASE_URL
sync_db_url_base = raw_db_url.replace("+asyncpg", "")
if "?" in sync_db_url_base:
    sync_db_url_base = sync_db_url_base.split("?")[0]

# This is the URL Alembic will use for its synchronous operations.
sync_url = sync_db_url_base

# Connect args for synchronous psycopg2 connection to set schema
sync_connect_args = {'options': '-csearch_path=public'}


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=sync_url, # Use the processed sync_url
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection"""
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in async mode.
    NOTE: Alembic's primary operations are synchronous. This function,
    if used, typically wraps synchronous engine logic for compatibility
    or specific async setup if absolutely needed, but standard Alembic
    relies on a synchronous DBAPI.
    The provided template had a synchronous create_engine here.
    """
    connectable = create_engine(
        sync_url, # Use the processed sync_url
        poolclass=pool.NullPool,
        connect_args=sync_connect_args # Apply schema setting
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        sync_url, # Use the processed sync_url
        connect_args=sync_connect_args # Apply schema setting
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
