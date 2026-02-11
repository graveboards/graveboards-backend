from functools import wraps
from typing import Callable, Awaitable, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ModelClass, BaseType
from .protocol import DatabaseProtocol


def session_manager(func: Callable[..., Awaitable[Any]]):
    @wraps(func)
    async def wrapper(self: DatabaseProtocol, *args, **kwargs):
        session = kwargs.get("session")

        if session is not None:
            return await func(self, *args, **kwargs)

        async with self.session() as session:
            kwargs["session"] = session
            return await func(self, *args, **kwargs)

    return wrapper


def ensure_required(many: bool = False):
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(model_class: ModelClass, session: AsyncSession, *args, **kwargs) -> BaseType:
            required_columns = model_class.required_columns

            def get_missing(d_: dict) -> list[str]:
                return [col for col in required_columns if col not in d_]

            if not many:
                missing_columns = get_missing(kwargs)

                if missing_columns:
                    raise ValueError(f"Missing required columns: {", ".join(missing_columns)}")
            else:
                for i, d in enumerate(args):
                    missing_columns = get_missing(d)

                    if missing_columns:
                        raise ValueError(f"Missing required columns at index {i}: {", ".join(missing_columns)}")

            return await func(model_class, session, *args, **kwargs)

        return wrapper

    return decorator
