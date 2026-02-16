from typing import Callable, Awaitable, ParamSpec, TypeVar, Concatenate
from functools import wraps

from .db import PostgresqlDB

P = ParamSpec("P")
R = TypeVar("R")


def db_lifespan(func: Callable[Concatenate[PostgresqlDB, P], Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        db = next((a for a in args if isinstance(a, PostgresqlDB)), None)

        if db is None:
            db = PostgresqlDB()
            args = (db, *args)

        try:
            return await func(*args, **kwargs)
        finally:
            await db.close()

    return wrapper
