__all__ = ["PostgresqlDB", "db_lifespan"]


def __getattr__(name):
    if name == "PostgresqlDB":
        from .db import PostgresqlDB

        return PostgresqlDB

    if name == "db_lifespan":
        from .lifespan import db_lifespan

        return db_lifespan

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
