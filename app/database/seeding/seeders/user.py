import os
import asyncio

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.database.models import User
from app.database.crud import session_manager, db_session_resolver
from app.database.seeding import SeederTarget
from app.database.seeding.event import SeedEvent
from .base import Seeder, FIXTURES_PATH


class UserSeeder(Seeder):
    @session_manager(session_resolver=db_session_resolver, autoflush_allowed=False)
    async def seed(self, queue: asyncio.Queue[SeedEvent | None], session: AsyncSession = None):
        self.session = session
        await queue.put(SeedEvent(SeederTarget.USER, self.progress, self.total))

        for user_entry in self.data:
            await self._seed_user(user_entry)
            self.progress += 1
            await queue.put(SeedEvent(SeederTarget.USER, self.progress, self.total))

    async def _seed_user(self, user_entry: dict):
        if not await self.db.get(User, id=user_entry["id"], session=self.session):
            await self.db.add(User, **user_entry, session=self.session)

    @property
    def fixture_path(self) -> str:
        return os.path.join(FIXTURES_PATH, "users.json")
