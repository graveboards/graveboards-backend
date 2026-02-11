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


def ensure_required(func: Callable):
    @wraps(func)
    async def wrapper(model_class: ModelClass, session: AsyncSession, **kwargs) -> BaseType:
        required_columns = model_class.get_required_columns()
        missing_columns = [col for col in required_columns if col not in kwargs]

        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        return await func(model_class, session, **kwargs)

    return wrapper
