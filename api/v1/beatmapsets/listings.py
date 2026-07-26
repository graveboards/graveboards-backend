from connexion import request
from starlette.requests import Request
from typing import Any
from starlette.responses import Response

from api.decorators import api_query
from api.utils import build_pydantic_include
from app.database import PostgresqlDB
from app.database.models import BeatmapsetListing, BeatmapsetSnapshot, ModelClass
from app.database.schemas import BeatmapsetSnapshotSchema
from app.spec import get_include_schema

__all__ = ["search"]


@api_query(ModelClass.BEATMAPSET_SNAPSHOT, many=True)
async def search(request: Request, **kwargs: Any) -> Response:
    db: PostgresqlDB = request.state.db

    beatmapset_snapshots = await db.get_many(
        BeatmapsetSnapshot,
        _join=(
            BeatmapsetListing,
            BeatmapsetListing.beatmapset_snapshot_id == BeatmapsetSnapshot.id,
        ),
        **kwargs,
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
