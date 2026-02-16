from typing import Protocol, AsyncContextManager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


class DatabaseProtocol(Protocol):
    engine: AsyncEngine

    def session(self, autoflush: bool = True) -> AsyncContextManager[AsyncSession]:
        ...
