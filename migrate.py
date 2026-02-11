import json
import asyncio
import logging
from datetime import datetime, timezone

from httpx import HTTPStatusError

from app.database import PostgresqlDB
from app.database.models import Beatmapset, BeatmapsetSnapshot, Request
from app.beatmap_manager import BeatmapManager
from app.redis import RedisClient
from app.logging import setup_logging
from setup import setup


async def migrate():
    setup_logging()
    logger = logging.getLogger("maintenance")
    logger.info("Starting migration...")

    rc = RedisClient()
    db = PostgresqlDB()

    with open("requests.json", "r") as file:
        rows = json.load(file)
        total_rows = len(rows)

        for i, row in enumerate(rows, start=1):
            beatmapset_id = row["beatmapset_id"]
            row["created_at"] = datetime.fromisoformat(row["created_at"]).replace(tzinfo=timezone.utc)
            row["updated_at"] = datetime.fromisoformat(row["updated_at"]).replace(tzinfo=timezone.utc)

            if not await db.get(Beatmapset, id=beatmapset_id):
                try:
                    bm = BeatmapManager(rc, db)
                    changelog = await bm.archive(beatmapset_id)
                    row["beatmapset_snapshot_id"] = changelog["snapshotted_beatmapset"]["id"]
                except HTTPStatusError as e:
                    if e.response.status_code == 404:
                        continue
            else:
                beatmapset_snapshot = await db.get(BeatmapsetSnapshot, id=beatmapset_id, _reversed=True)

                if beatmapset_snapshot is None:
                    raise ValueError(f"BeatmapsetSnapshot for beatmapset {beatmapset_id} not found")

                row["beatmapset_snapshot_id"] = beatmapset_snapshot.id

            if not await db.get(Request, **row):
                await db.add(Request, **row)

            progress = int((i / total_rows) * 100)
            bar = "=" * (progress // 2)
            spaces = " " * (50 - len(bar))

            logger.info(f"[requests] [{bar}{spaces}] {progress}% ({i}/{total_rows})")

    logger.info("Migration complete!")


if __name__ == "__main__":
    asyncio.run(setup())
    asyncio.run(migrate())
