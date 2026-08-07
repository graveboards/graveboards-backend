"""Serve .osu files for beatmap snapshots."""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

import aiofiles
from connexion import request
from starlette.responses import PlainTextResponse

from api.decorators import coerce_arguments
from app.beatmaps import BeatmapManager
from app.database.models import BeatmapSnapshot
from app.exceptions import NotFound

if TYPE_CHECKING:
    from api.http_types import APIResponse
    from app.database import PostgresqlDB
    from app.redis_client import RedisClient

__all__ = ["search"]


@coerce_arguments(snapshot_number={"latest": -1})
async def search(beatmap_id: int, snapshot_number: int = -1) -> APIResponse:
    """Serve the .osu file for a beatmap snapshot.

    Returns:
        Tuple of (file content, status code, headers).
    """
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _order_by=BeatmapSnapshot.snapshot_number.desc(),
            _offset=offset,
        )
    else:
        beatmap_snapshot = await db.get(
            BeatmapSnapshot, beatmap_id=beatmap_id, snapshot_number=snapshot_number
        )

    if not beatmap_snapshot:
        raise NotFound(
            f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' not found"
        )

    snapshot_number = beatmap_snapshot.snapshot_number

    bm = BeatmapManager(rc, db)
    dotosu_file_path = bm.get_path(beatmap_id, snapshot_number)

    try:
        async with aiofiles.open(dotosu_file_path, "rb") as file:
            dotosu_file_data = await file.read()
    except FileNotFoundError as e:
        raise NotFound(f"Beatmap .osu file not found: {beatmap_id}/{snapshot_number}.osu") from e

    dotosu_file_io = BytesIO(dotosu_file_data)
    dotosu_file_io.seek(0)

    return PlainTextResponse(content=dotosu_file_io.read().decode())  # type: ignore[return-value]
