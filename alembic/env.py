from __future__ import annotations

import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# --- Path setup (ensure 'app' package is importable) ---
# env.py is in app/alembic/, so project root is two levels up
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# --- Load .env early ---
load_dotenv()

# --- Alembic config ---
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# --- Import DB and models ---
from app.database import Base, DATABASE_URL  # noqa

# IMPORTANT: import models so they register on Base.metadata
# (User, Role, Permission, association tables, etc.)
import app.models  # noqa  # side-effect import to populate Base.metadata

# Inject URL from env / app config
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Alembic 1.11+ prefers config.get_section(config.config_ini_section)
    section = config.get_section(getattr(config, "config_ini_section", "alembic")) or {}
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
