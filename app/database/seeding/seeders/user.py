"""Seeder for user fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from app.database.crud import db_session_resolver, session_manager
from app.database.models import User
from app.database.seeding.event import SeedEvent
from app.database.seeding.target import SeederTarget

from .base import Seeder

if TYPE_CHECKING:
    import asyncio

    from sqlalchemy.ext.asyncio.session import AsyncSession


class UserSeeder(Seeder):
    """Seed users from fixtures."""

    @session_manager(session_resolver=db_session_resolver, autoflush_allowed=False)
    @override
    async def seed(
        self, queue: asyncio.Queue[SeedEvent | None], session: AsyncSession | None = None
    ) -> None:
        self.session = session
        await queue.put(SeedEvent(SeederTarget.USER, self.progress, self.total))

        for user_entry in self.data:
            await self._seed_user(user_entry)
            self.progress += 1
            await queue.put(SeedEvent(SeederTarget.USER, self.progress, self.total))

    async def _seed_user(self, user_entry: dict[str, Any]) -> None:
        if not await self.db.get(User, id=user_entry["id"], session=self.session):
            await self.db.add(User, **user_entry, session=self.session)
