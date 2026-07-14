import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.database import PostgresqlDB
from app.database.seeding.event import SeedEvent


class Seeder(ABC):
    def __init__(self, db: PostgresqlDB):
        self.db = db
        self.data: list[dict] = []
        self.progress: int = 0
        self.total: int = 0
        self.queue: asyncio.Queue | None = None
        self.session: AsyncSession | None = None

    def set_data(self, data: list[dict]) -> None:
        """Inject fixture data loaded by the fixture loader."""
        self.data = data
        self.total = len(self.data)

    @abstractmethod
    async def seed(self, queue: asyncio.Queue[SeedEvent | None], session: AsyncSession = None):
        ...

    @staticmethod
    def _normalize_datetimes(obj):
        """Recursively convert ISO datetime strings to datetime objects.

        Safety net for any fixture data that still contains string dates.
        """
        if isinstance(obj, dict):
            return {k: Seeder._normalize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [Seeder._normalize_datetimes(item) for item in obj]
        elif isinstance(obj, str):
            try:
                return datetime.fromisoformat(obj)
            except ValueError:
                return obj
        return obj
