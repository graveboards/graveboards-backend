from starlette.responses import StreamingResponse
from connexion import request

from api.decorators import coerce_arguments
from app.beatmap_manager import BeatmapManager
from app.database import PostgresqlDB
from app.redis import RedisClient
from app.utils import stream_file


@coerce_arguments(snapshot_number={"latest": -1})
async def search(beatmapset_id: int, snapshot_number: int = -1):
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    try:
        bm = BeatmapManager(rc, db)
        zip_file_io = await bm.get_zip(beatmapset_id, snapshot_number)
    except ValueError:
        return {"message": f"BeatmapsetSnapshot with beatmapset_id '{beatmapset_id}' and snapshot_number '{snapshot_number}' not found"}, 404

    return StreamingResponse(
        content=stream_file(zip_file_io),
        headers={"Content-Disposition": f"attachment; filename={beatmapset_id}.zip"},
        media_type="application/zip"
    )
