import asyncio

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.database.models import Request, BeatmapsetSnapshot
from app.database.crud import session_manager, db_session_resolver
from app.database.seeding import SeederTarget
from app.database.seeding.event import SeedEvent
from .base import Seeder


class RequestSeeder(Seeder):
    @session_manager(session_resolver=db_session_resolver, autoflush_allowed=False)
    async def seed(self, queue: asyncio.Queue[SeedEvent | None], session: AsyncSession = None):
        self.session = session
        await queue.put(SeedEvent(SeederTarget.REQUEST, self.progress, self.total))

        for request_entry in self.data:
            await self._seed_request(request_entry)
            self.progress += 1
            await queue.put(SeedEvent(SeederTarget.REQUEST, self.progress, self.total))

    async def _seed_request(self, request_entry: dict):
        beatmapset_id = request_entry["beatmapset_id"]

        if not await self.db.get(
            Request,
            beatmapset_id=beatmapset_id,
            queue_id=request_entry["queue_id"],
            session=self.session
        ):
            beatmapset_snapshot = await self.db.get(
                BeatmapsetSnapshot,
                beatmapset_id=beatmapset_id,
                _sorting=[{"field": "BeatmapsetSnapshot.id", "order": "desc"}],
                session=self.session
            )
            if beatmapset_snapshot is None:
                self.logger.warning(
                    f"Skipping request {request_entry['id']}: "
                    f"no BeatmapsetSnapshot for beatmapset {beatmapset_id}"
                )
                return
            request_entry["beatmapset_snapshot_id"] = beatmapset_snapshot.id
            await self.db.add(Request, **request_entry, session=self.session)
