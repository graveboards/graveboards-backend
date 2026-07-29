from __future__ import annotations
from typing import Any

__all__ = ["PostgresqlDB", "db_lifespan"]


def __getattr__(name: str) -> Any:
    if name == "PostgresqlDB":
        from .db import PostgresqlDB

        return PostgresqlDB

    if name == "db_lifespan":
        from .lifespan import db_lifespan

        return db_lifespan

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
