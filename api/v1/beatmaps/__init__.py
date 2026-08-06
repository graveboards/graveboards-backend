"""Re-exports for the beatmaps v1 API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from api.decorators import api_query
from api.utils import build_pydantic_include
from app.database.models import Beatmap, ModelClass

if TYPE_CHECKING:
    from starlette.requests import Request

    from api.http_types import APIResponse
    from app.database import PostgresqlDB
from app.database.schemas import BeatmapSchema
from app.exceptions import NotFound
from app.spec import get_include_schema

from . import listings, snapshots, tags

__all__ = ["get", "listings", "search", "snapshots", "tags"]


@api_query(ModelClass.BEATMAP, many=True)
async def search(request: Request, **kwargs: Any) -> APIResponse:
    """Search for beatmaps.

    Returns:
        Tuple of (beatmaps data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    beatmaps = await db.get_many(Beatmap, **kwargs)

    if not beatmaps:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=beatmaps[0],
        include_schema=get_include_schema(ModelClass.BEATMAP),
        request_include=kwargs.get("_include"),
    )

    beatmaps_data = [
        BeatmapSchema.model_validate(beatmap).model_dump(include=include) for beatmap in beatmaps
    ]

    return beatmaps_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.BEATMAP)
async def get(request: Request, beatmap_id: int, **kwargs: Any) -> APIResponse:
    """Get a single beatmap by ID.

    Returns:
        Tuple of (beatmap data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    beatmap = await db.get(Beatmap, id=beatmap_id, **kwargs)

    if not beatmap:
        raise NotFound(f"Beatmap with beatmap_id '{beatmap_id}' not found")

    include = build_pydantic_include(
        obj=beatmap,
        include_schema=get_include_schema(ModelClass.BEATMAP),
        request_include=kwargs.get("_include"),
    )

    beatmap_data = BeatmapSchema.model_validate(beatmap).model_dump(include=include)

    return beatmap_data, 200, {"Content-Type": "application/json"}
