from __future__ import annotations
from starlette.requests import Request
from starlette.responses import StreamingResponse
from app.types import APIResponse

from api.decorators import coerce_arguments
from app.beatmaps import BeatmapManager
from app.database import PostgresqlDB
from app.exceptions import NotFound
from app.redis_client import RedisClient
from app.utils import stream_file

__all__ = ["search"]


@coerce_arguments(snapshot_number={"latest": -1})
async def search(request: Request, beatmapset_id: int, snapshot_number: int = -1) -> APIResponse:
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    try:
        bm = BeatmapManager(rc, db)
        zip_file_io = await bm.get_zip(beatmapset_id, snapshot_number)
    except ValueError as e:
        raise NotFound(
            f"BeatmapsetSnapshot with beatmapset_id '{beatmapset_id}' and snapshot_number '{snapshot_number}' not found"
        ) from e

    return StreamingResponse(
        content=stream_file(zip_file_io),
        headers={"Content-Disposition": f"attachment; filename={beatmapset_id}.zip"},
        media_type="application/zip",
    )
