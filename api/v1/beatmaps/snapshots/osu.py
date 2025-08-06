from io import BytesIO

import aiofiles
from starlette.responses import PlainTextResponse
from connexion import request

from app.beatmap_manager import BeatmapManager
from app.database import PostgresqlDB
from app.redis import RedisClient


async def search(beatmap_id: int, snapshot_number: int):
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    if not await db.get_beatmap_snapshot(beatmap_id=beatmap_id, snapshot_number=snapshot_number):
        return {"message": f"There is no beatmap snapshot with beatmap ID '{beatmap_id}' and snapshot number '{snapshot_number}'"}, 404

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
