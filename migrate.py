import json
import asyncio
from datetime import datetime, timezone

from httpx import HTTPStatusError

from app.database import PostgresqlDB
from app.database.models import Beatmapset, BeatmapsetSnapshot, Request
from app.beatmaps import BeatmapManager
from app.redis import RedisClient
from app.logging import setup_logging
from app.setup import setup
from app.logging import get_logger


async def migrate():
    logger = get_logger("migrate")
    logger.info("Starting migration...")

    with open("requests.json", "r") as file:
        rows: list[dict] = sorted(json.load(file), key=lambda r: r["id"])
        total_rows = len(rows)

    rc = RedisClient()
    db = PostgresqlDB()

    try:
        for i, row in enumerate(rows, start=1):
            beatmapset_id = row["beatmapset_id"]
            row["created_at"] = datetime.fromisoformat(row["created_at"]).replace(tzinfo=timezone.utc)
            row["updated_at"] = datetime.fromisoformat(row["updated_at"]).replace(tzinfo=timezone.utc)

            async with db.session() as session:
                if not await db.get(Beatmapset, id=beatmapset_id, session=session):
                    try:
                        bm = BeatmapManager(rc, db)
                        changelog = await bm.archive(beatmapset_id)
                        row["beatmapset_snapshot_id"] = changelog["snapshotted_beatmapset"]["id"]
                    except HTTPStatusError as e:
                        if e.response.status_code == 404:
                            continue
                else:
                    beatmapset_snapshot = await db.get(
                        BeatmapsetSnapshot,
                        beatmapset_id=beatmapset_id,
                        _sorting=[{"field": "BeatmapsetSnapshot.id", "order": "desc"}],
                        session=session
                    )

                    if beatmapset_snapshot is None:
                        raise ValueError(f"BeatmapsetSnapshot for beatmapset {beatmapset_id} not found")

                    row["beatmapset_snapshot_id"] = beatmapset_snapshot.id

                if not await db.get(Request, **row, session=session):
                    await db.add(Request, **row, session=session)

            progress = int((i / total_rows) * 100)
            bar = "=" * (progress // 2)
            spaces = " " * (50 - len(bar))
            logger.info(f"[requests] [{bar}{spaces}] {progress}% ({i}/{total_rows})")

        logger.info("Migration complete!")
    finally:
        await rc.close()
        await db.close()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(setup())
    asyncio.run(migrate())
