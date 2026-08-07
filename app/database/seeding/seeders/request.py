"""Seeder for request fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from app.database.crud import db_session_resolver, session_manager
from app.database.models import BeatmapsetSnapshot, Queue, Request
from app.database.seeding.event import SeedEvent
from app.database.seeding.target import SeederTarget

from .base import Seeder

if TYPE_CHECKING:
    import asyncio

    from sqlalchemy.ext.asyncio.session import AsyncSession


class RequestSeeder(Seeder):
    """Seed requests from fixtures."""

    @session_manager(session_resolver=db_session_resolver, autoflush_allowed=False)
    @override
    async def seed(
        self, queue: asyncio.Queue[SeedEvent | None], session: AsyncSession | None = None
    ) -> None:
        self.session = session
        await queue.put(SeedEvent(SeederTarget.REQUEST, self.progress, self.total))

        for request_entry in self.data:
            await self._seed_request(request_entry)
            self.progress += 1
            await queue.put(SeedEvent(SeederTarget.REQUEST, self.progress, self.total))

    async def _seed_request(self, request_entry: dict[str, Any]) -> None:
        beatmapset_id = request_entry["beatmapset_id"]

        queue = await self.db.get(
            Queue,
            user_id=request_entry["queue_user_id"],
            name=request_entry["queue_name"],
            session=self.session,
        )
        if queue is None:
            self.logger.warning(
                f"Skipping request for beatmapset {beatmapset_id}: "
                f"no Queue found for user_id={request_entry['queue_user_id']} "
                f"name={request_entry['queue_name']}"
            )
            return

        if not await self.db.get(
            Request,
            beatmapset_id=beatmapset_id,
            queue_id=queue.id,
            session=self.session,
        ):
            beatmapset_snapshot = await self.db.get(
                BeatmapsetSnapshot,
                beatmapset_id=beatmapset_id,
                _sorting=[{"field": "BeatmapsetSnapshot.id", "order": "desc"}],
                session=self.session,
            )
            if beatmapset_snapshot is None:
                self.logger.warning(
                    f"Skipping request for beatmapset {beatmapset_id}: "
                    f"no BeatmapsetSnapshot for beatmapset {beatmapset_id}"
                )
                return

            request_data = {
                k: v for k, v in request_entry.items() if k not in {"queue_user_id", "queue_name"}
            }
            request_data["queue_id"] = queue.id
            request_data["beatmapset_snapshot_id"] = beatmapset_snapshot.id
            await self.db.add(Request, **request_data, session=self.session)
