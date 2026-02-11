from io import BytesIO

import aiofiles
from starlette.responses import PlainTextResponse
from connexion import request

from app.beatmap_manager import BeatmapManager
from app.database import PostgresqlDB
from app.database.models import BeatmapSnapshot
from app.redis import RedisClient


async def search(beatmap_id: int, snapshot_number: int):
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _order_by=BeatmapSnapshot.snapshot_number.desc(),
            _offset=offset
        )
    else:
        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            snapshot_number=snapshot_number
        )

    snapshot_number = beatmap_snapshot.snapshot_number

    bm = BeatmapManager(rc, db)
    dotosu_file_path = bm.get_path(beatmap_id, snapshot_number)

    try:
        async with aiofiles.open(dotosu_file_path, "rb") as file:
            dotosu_file_data = await file.read()
    except FileNotFoundError:
        return {"message": f"Beatmap .osu file not found: {beatmap_id}/{snapshot_number}.osu"}, 404

    dotosu_file_io = BytesIO(dotosu_file_data)
    dotosu_file_io.seek(0)

    return PlainTextResponse(content=dotosu_file_io.read().decode())
