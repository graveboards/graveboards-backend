import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add the project root to sys.path so we can import app modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Add your model's MetaData object here for 'autogenerate' support
# Import Base directly from the base module to avoid circular imports
from app.database.models.base import Base  # noqa: E402
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_sqlalchemy_url() -> str:
    """Get the SQLAlchemy URL from the application config.

    Uses psycopg2 (synchronous) for migrations instead of asyncpg (async).
    """
    from app.config import POSTGRESQL_CONFIGURATION
    from sqlalchemy import URL

    # Override drivername to use synchronous psycopg2 for migrations
    config = POSTGRESQL_CONFIGURATION.copy()
    config["drivername"] = "postgresql+psycopg2"

    url = URL.create(**config)
    return url.render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_sqlalchemy_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = get_sqlalchemy_url()
    connectable = engine_from_config(
        {"url": url},
        prefix="",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
