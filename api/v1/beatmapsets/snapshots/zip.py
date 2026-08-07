"""Serve zip downloads for beatmapset snapshots."""

from __future__ import annotations

from typing import TYPE_CHECKING

from connexion import request
from starlette.responses import StreamingResponse

from api.decorators import coerce_arguments
from app.beatmaps import BeatmapManager
from app.exceptions import NotFound

if TYPE_CHECKING:
    from api.http_types import APIResponse
    from app.database import PostgresqlDB
    from app.redis_client import RedisClient
from app.utils import stream_file

__all__ = ["search"]


@coerce_arguments(snapshot_number={"latest": -1})
async def search(beatmapset_id: int, snapshot_number: int = -1) -> APIResponse:
    """Serve a zip download for a beatmapset snapshot.

    Returns:
        Tuple of (streaming response, status code, headers).
    """
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    try:
        bm = BeatmapManager(rc, db)
        zip_file_io = await bm.get_zip(beatmapset_id, snapshot_number)
    except ValueError as e:
        raise NotFound(
            f"BeatmapsetSnapshot with beatmapset_id '{beatmapset_id}' and snapshot_number '{snapshot_number}' not found"
        ) from e

    return StreamingResponse(  # type: ignore[return-value]
        content=stream_file(zip_file_io),
        headers={"Content-Disposition": f"attachment; filename={beatmapset_id}.zip"},
        media_type="application/zip",
    )
