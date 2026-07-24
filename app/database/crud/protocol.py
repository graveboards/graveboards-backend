from contextlib import AbstractAsyncContextManager
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


class DatabaseProtocol(Protocol):
    engine: AsyncEngine

    def session(self, autoflush: bool = True) -> AbstractAsyncContextManager[AsyncSession]: ...
