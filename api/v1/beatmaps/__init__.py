from connexion import request

from api.decorators import api_query
from api.utils import build_pydantic_include
from app.exceptions import NotFound
from app.spec import get_include_schema
from app.database import PostgresqlDB
from app.database.models import Beatmap, ModelClass
from app.database.schemas import BeatmapSchema
from . import snapshots, listings, tags


@api_query(ModelClass.BEATMAP, many=True)
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    beatmaps = await db.get_many(
        Beatmap,
        **kwargs
    )

    if not beatmaps:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=beatmaps[0],
        include_schema=get_include_schema(ModelClass.BEATMAP),
        request_include=kwargs.get("_include")
    )

    beatmaps_data = [
        BeatmapSchema.model_validate(beatmap).model_dump(include=include)
        for beatmap in beatmaps
    ]

    return beatmaps_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.BEATMAP)
async def get(beatmap_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    beatmap = await db.get(
        Beatmap,
        id=beatmap_id,
        **kwargs
    )

    if not beatmap:
        raise NotFound(f"Beatmap with beatmap_id '{beatmap_id}' not found")

    include = build_pydantic_include(
        obj=beatmap,
        include_schema=get_include_schema(ModelClass.BEATMAP),
        request_include=kwargs.get("_include")
    )

    beatmap_data = BeatmapSchema.model_validate(beatmap).model_dump(include=include)

    return beatmap_data, 200, {"Content-Type": "application/json"}
