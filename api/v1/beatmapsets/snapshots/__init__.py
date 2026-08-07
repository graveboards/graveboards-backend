"""Re-exports for the beatmapsets snapshots v1 API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from connexion import request

from api.decorators import api_query, coerce_arguments
from api.utils import build_pydantic_include
from app.database.models import BeatmapsetSnapshot, ModelClass

if TYPE_CHECKING:
    from api.http_types import APIResponse
    from app.database import PostgresqlDB
from app.database.schemas import BeatmapsetSnapshotSchema
from app.exceptions import NotFound
from app.spec import get_include_schema

from . import zip as zip_snapshots

__all__ = ["get", "search", "zip_snapshots"]


@api_query(ModelClass.BEATMAPSET_SNAPSHOT, many=True)
async def search(beatmapset_id: int, **kwargs: Any) -> APIResponse:
    """Search for beatmapset snapshots by beatmapset ID.

    Returns:
        Tuple of (snapshots data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    beatmapset_snapshots = await db.get_many(
        BeatmapsetSnapshot, beatmapset_id=beatmapset_id, **kwargs
    )

    if not beatmapset_snapshots:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=beatmapset_snapshots[0],
        include_schema=get_include_schema(ModelClass.BEATMAPSET_SNAPSHOT),
        request_include=kwargs.get("_include"),
    )

    beatmapset_snapshots_data = [
        BeatmapsetSnapshotSchema.model_validate(beatmapset_snapshot).model_dump(include=include)
        for beatmapset_snapshot in beatmapset_snapshots
    ]

    return beatmapset_snapshots_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.BEATMAPSET_SNAPSHOT)
@coerce_arguments(snapshot_number={"latest": -1})
async def get(beatmapset_id: int, snapshot_number: int = -1, **kwargs: Any) -> APIResponse:
    """Get a single beatmapset snapshot by beatmapset ID and snapshot number.

    Returns:
        Tuple of (snapshot data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmapset_snapshot = await db.get(
            BeatmapsetSnapshot,
            beatmapset_id=beatmapset_id,
            _order_by=BeatmapsetSnapshot.snapshot_number.desc(),
            _offset=offset,
            **kwargs,
        )
    else:
        beatmapset_snapshot = await db.get(
            BeatmapsetSnapshot,
            beatmapset_id=beatmapset_id,
            snapshot_number=snapshot_number,
            **kwargs,
        )

    if not beatmapset_snapshot:
        raise NotFound(
            f"BeatmapsetSnapshot with beatmapset_id '{beatmapset_id}' and snapshot_number '{snapshot_number}' not found"
        )

    include = build_pydantic_include(
        obj=beatmapset_snapshot,
        include_schema=get_include_schema(ModelClass.BEATMAPSET_SNAPSHOT),
        request_include=kwargs.get("_include"),
    )

    beatmapset_snapshot_data = BeatmapsetSnapshotSchema.model_validate(
        beatmapset_snapshot
    ).model_dump(include=include)

    return beatmapset_snapshot_data, 200, {"Content-Type": "application/json"}
