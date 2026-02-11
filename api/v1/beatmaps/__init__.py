from connexion import request

from api.utils import build_pydantic_include
from app.spec import get_include_schema
from app.database import PostgresqlDB
from app.database.models import Beatmap, ModelClass
from app.database.schemas import BeatmapSchema
from . import snapshots



async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

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

    return beatmaps_data, 200
