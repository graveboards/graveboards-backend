import asyncio
import os
import json
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.database import PostgresqlDB
from app.database.seeding.event import SeedEvent

FIXTURES_PATH = os.path.abspath("app/database/seeding/fixtures")


class Seeder(ABC):
    def __init__(self, db: PostgresqlDB):
        self.db = db
        self.data = self._load()
        self.progress: int = 0
        self.total = len(self.data)
        self.queue: asyncio.Queue | None = None
        self.session: AsyncSession | None = None

    @abstractmethod
    async def seed(self, queue: asyncio.Queue[SeedEvent | None], session: AsyncSession = None):
        ...

    def _load(self) -> list[dict]:
        with open(self.fixture_path) as f:
            return json.load(f)

    @property
    @abstractmethod
    def fixture_path(self) -> str:
        ...
