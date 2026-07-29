from __future__ import annotations
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, Concatenate, ParamSpec, TypeVar

from .db import PostgresqlDB

P = ParamSpec("P")
R = TypeVar("R")


def db_lifespan[**P, R](
    func: Callable[Concatenate[PostgresqlDB, P], Awaitable[R]],
) -> Callable[P, Awaitable[R]]:
    """Ensure a PostgresqlDB lifecycle around an async function.

    If a PostgresqlDB instance is not provided in the function's arguments, one is
    created automatically. The database engine is disposed after completion.

    Args:
        func: Async function requiring a PostgresqlDB instance.

    Returns:
        Wrapped async function with automatic DB lifecycle handling.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> R:
        db = next((a for a in args if isinstance(a, PostgresqlDB)), None)

        if db is None:
            return await func(PostgresqlDB(), *args, **kwargs)

        try:
            return await func(db, *args, **kwargs)
        finally:
            await db.close()

    return wrapper
