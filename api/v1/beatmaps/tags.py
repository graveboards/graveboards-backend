from connexion import request

from api.decorators import api_query
from api.utils import build_pydantic_include
from app.database import PostgresqlDB
from app.database.models import ModelClass, BeatmapTag
from app.database.schemas import BeatmapTagSchema
from app.exceptions import NotFound
from app.spec import get_include_schema


@api_query(ModelClass.BEATMAP_TAG, many=True)
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    beatmap_tags = await db.get_many(
        BeatmapTag,
        **kwargs
    )

    if not beatmap_tags:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=beatmap_tags[0],
        include_schema=get_include_schema(ModelClass.BEATMAP_TAG),
        request_include=kwargs.get("_include")
    )

    beatmap_tags_data = [
        BeatmapTagSchema.model_validate(beatmap_tag).model_dump(include=include)
        for beatmap_tag in beatmap_tags
    ]

    return beatmap_tags_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.BEATMAP_TAG)
async def get(beatmap_tag_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    beatmap_tag = await db.get(
        BeatmapTag,
        id=beatmap_tag_id,
        **kwargs
    )

    if not beatmap_tag:
        raise NotFound(f"BeatmapTag with id '{beatmap_tag_id}' not found")

    include = build_pydantic_include(
        obj=beatmap_tag,
        include_schema=get_include_schema(ModelClass.BEATMAP_TAG),
        request_include=kwargs.get("_include")
    )

    beatmap_tag_data = BeatmapTagSchema.model_validate(beatmap_tag).model_dump(include=include)

    return beatmap_tag_data, 200, {"Content-Type": "application/json"}
