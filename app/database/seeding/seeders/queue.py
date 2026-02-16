import os
import asyncio

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.database.models import Queue
from app.database.crud import session_manager, db_session_resolver
from app.database.seeding import SeederTarget
from app.database.seeding.event import SeedEvent
from .base import Seeder, FIXTURES_PATH


class QueueSeeder(Seeder):
    @session_manager(session_resolver=db_session_resolver, autoflush_allowed=False)
    async def seed(self, queue: asyncio.Queue[SeedEvent | None], session: AsyncSession = None):
        self.session = session
        await queue.put(SeedEvent(SeederTarget.QUEUE, self.progress, self.total))

        for queue_entry in self.data:
            await self._seed_queue(queue_entry)
            self.progress += 1
            await queue.put(SeedEvent(SeederTarget.QUEUE, self.progress, self.total))

    async def _seed_queue(self, queue_entry: dict):
        if not await self.db.get(
            Queue,
            user_id=queue_entry["user_id"],
            name=queue_entry["name"],
            session=self.session
        ):
            await self.db.add(Queue, **queue_entry, session=self.session)

    @property
    def fixture_path(self) -> str:
        return os.path.join(FIXTURES_PATH, "queues.json")
