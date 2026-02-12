import asyncio
from abc import ABC, abstractmethod

from app.redis import RedisClient
from app.database import PostgresqlDB
from .enums import RuntimeTaskName


class Service(ABC):
    def __init__(self, rc: RedisClient, db: PostgresqlDB):
        self.rc = rc
        self.db = db

        self.runtime_tasks: dict[RuntimeTaskName, asyncio.Task] = {}

    @abstractmethod
    async def run(self):
        ...

    async def stop(self):
        for task in self.runtime_tasks.values():
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass
