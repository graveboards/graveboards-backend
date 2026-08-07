"""Seeder for queue fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from app.database.crud import db_session_resolver, session_manager
from app.database.models import Queue
from app.database.seeding.target import SeederTarget
from app.database.seeding.event import SeedEvent

from .base import Seeder

if TYPE_CHECKING:
    import asyncio

    from sqlalchemy.ext.asyncio.session import AsyncSession


class QueueSeeder(Seeder):
    """Seed queues from fixtures."""

    @session_manager(session_resolver=db_session_resolver, autoflush_allowed=False)
    @override
    async def seed(
        self, queue: asyncio.Queue[SeedEvent | None], session: AsyncSession | None = None
    ) -> None:
        self.session = session
        await queue.put(SeedEvent(SeederTarget.QUEUE, self.progress, self.total))

        for queue_entry in self.data:
            await self._seed_queue(queue_entry)
            self.progress += 1
            await queue.put(SeedEvent(SeederTarget.QUEUE, self.progress, self.total))

    async def _seed_queue(self, queue_entry: dict[str, Any]) -> None:
        if not await self.db.get(
            Queue, user_id=queue_entry["user_id"], name=queue_entry["name"], session=self.session
        ):
            await self.db.add(Queue, **queue_entry, session=self.session)
