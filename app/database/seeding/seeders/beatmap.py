import os
import json
import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.database import PostgresqlDB
from app.database.models import BeatmapTag, Beatmapset, Beatmap, BeatmapsetSnapshot, BeatmapSnapshot
from app.database.crud import session_manager, db_session_resolver
from app.database.seeding import SeederTarget
from app.database.seeding.event import SeedEvent
from .base import Seeder

BEATMAP_TAGS_PATH = Path("instance/fixtures/beatmap_tags.json")


class BeatmapSeeder(Seeder):
    def __init__(self, db: PostgresqlDB):
        super().__init__(db)
        self._beatmap_tags: list[dict] = []

    def set_data(self, data: list[dict]) -> None:
        """Inject fixture data loaded by the fixture loader."""
        super().set_data(data)
        self.total = len([bm for bs in self.data for bm in bs.get("beatmaps", [])])

    def set_beatmap_tags(self, tags: list[dict]) -> None:
        """Inject beatmap tag data loaded by the fixture loader."""
        self._beatmap_tags = tags

    @session_manager(session_resolver=db_session_resolver, autoflush_allowed=False)
    async def seed(self, queue: asyncio.Queue[SeedEvent | None], session: AsyncSession = None):
        self.queue = queue
        self.session = session
        await queue.put(SeedEvent(SeederTarget.BEATMAP, self.progress, self.total))
        await self._seed_beatmap_tags()

        for beatmapset_entry in self.data:
            await self._seed_beatmapset(beatmapset_entry)

    async def _seed_beatmap_tags(self):
        if self._beatmap_tags:
            tag_data = self._beatmap_tags
        elif BEATMAP_TAGS_PATH.exists():
            with open(BEATMAP_TAGS_PATH) as f:
                tag_data = json.load(f)
            tag_data = Seeder._normalize_datetimes(tag_data)
        else:
            return

        for beatmap_tag_entry in tag_data:
            if not await self.db.get(BeatmapTag, id=beatmap_tag_entry["id"], session=self.session):
                await self.db.add(BeatmapTag, **beatmap_tag_entry, session=self.session)

    async def _seed_beatmapset(self, beatmapset_entry: dict):
        beatmapset_id = beatmapset_entry["id"]
        user_id = beatmapset_entry["user_id"]

        if not await self.db.get(Beatmapset, id=beatmapset_id, session=self.session):
            await self.db.add(Beatmapset, id=beatmapset_id, user_id=user_id, session=self.session)

        bms_bm_mapping: dict[int, list[dict]] = {}

        for beatmap_entry in beatmapset_entry["beatmaps"]:
            added_bm_dict = await self._seed_beatmap(beatmap_entry)
            bms_bm_mapping.setdefault(beatmapset_id, []).extend(added_bm_dict)

        for beatmapset_snapshot_entry in beatmapset_entry["snapshots"]:
            await self._seed_beatmapset_snapshot(beatmapset_snapshot_entry, bms_bm_mapping)

    async def _seed_beatmap(self, beatmap_entry: dict) -> list[dict]:
        beatmap_id = beatmap_entry["id"]
        beatmapset_id = beatmap_entry["beatmapset_id"]

        if not await self.db.get(Beatmap, id=beatmap_id, session=self.session):
            await self.db.add(Beatmap, id=beatmap_id, beatmapset_id=beatmapset_id, session=self.session)

        added_bm_dicts: list[dict] = []
        snapshots = beatmap_entry.get("snapshots", [])

        for beatmap_snapshot_entry in snapshots:
            added_bm_dict = await self._seed_beatmap_snapshot(beatmap_snapshot_entry)
            added_bm_dicts.append(added_bm_dict)
            self.progress += 1
            await self.queue.put(SeedEvent(SeederTarget.BEATMAP, self.progress, self.total))

        return added_bm_dicts

    async def _seed_beatmapset_snapshot(self, beatmapset_snapshot_entry: dict, bm_bms_mapping: dict[int, list[dict]]):
        beatmapset_snapshot_entry["beatmap_snapshots"] = bm_bms_mapping[beatmapset_snapshot_entry["beatmapset_id"]]

        if not await self.db.get(BeatmapsetSnapshot, checksum=beatmapset_snapshot_entry["checksum"], session=self.session):
            await self.db.add(BeatmapsetSnapshot, **beatmapset_snapshot_entry, session=self.session)

    async def _seed_beatmap_snapshot(self, beatmap_snapshot_entry: dict) -> dict:
        checksum = beatmap_snapshot_entry["checksum"]

        beatmap_snapshot = await self.db.get(BeatmapSnapshot, checksum=checksum, session=self.session)

        if not beatmap_snapshot:
            beatmap_snapshot = await self.db.add(BeatmapSnapshot, **beatmap_snapshot_entry, session=self.session)

        return {"id": beatmap_snapshot.id}
