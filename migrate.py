import json
import asyncio
import sys
from datetime import datetime, timezone

from httpx import HTTPStatusError

from app.database import PostgresqlDB
from app.database.models import Beatmapset, BeatmapsetSnapshot, Request, User
from app.beatmaps import BeatmapManager
from app.redis import RedisClient
from app.logging import setup_logging
from app.setup import setup
from app.logging import get_logger

TIMEOUT_SECS = 60.0


async def migrate(input_path: str = "requests.json"):
    logger = get_logger("migrate")
    logger.info("Starting migration...")

    with open(input_path, "r") as file:
        rows: list[dict] = sorted(json.load(file), key=lambda r: r["id"])
        total_rows = len(rows)

    rc = RedisClient()
    db = PostgresqlDB()

    try:
        for i, row in enumerate(rows, start=1):
            beatmapset_id = row["beatmapset_id"]
            user_id = row["user_id"]
            row["created_at"] = datetime.fromisoformat(row["created_at"]).replace(tzinfo=timezone.utc)
            row["updated_at"] = datetime.fromisoformat(row["updated_at"]).replace(tzinfo=timezone.utc)

            async with db.session() as session:
                if not await db.get(User, id=user_id, session=session):
                    await db.add(User, id=user_id, session=session)
                    logger.debug(f"Added user: {user_id}")

                if not await db.get(Beatmapset, id=beatmapset_id, session=session):
                    try:
                        bm = BeatmapManager(rc, db)
                        changelog = await asyncio.wait_for(
                            bm.archive(beatmapset_id),
                            timeout=TIMEOUT_SECS
                        )
                        row["beatmapset_snapshot_id"] = changelog["snapshotted_beatmapset"]["id"]
                    except (HTTPStatusError, asyncio.TimeoutError) as e:
                        if isinstance(e, HTTPStatusError) and e.response.status_code == 404:
                            logger.warning(f"Beatmapset {beatmapset_id} not found, skipping")
                            continue
                        else:
                            logger.error(f"Error archiving beatmapset {beatmapset_id}: {e}, skipping")
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
        await rc.aclose()
        await db.close()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(setup())
    
    requests_input_path = sys.argv[1] if len(sys.argv) > 1 else "requests.json"
    asyncio.run(migrate(requests_input_path))
