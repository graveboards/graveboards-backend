from connexion import request

from api.decorators import api_query
from api.utils import build_pydantic_include
from app.database import PostgresqlDB
from app.database.models import ModelClass, BeatmapsetTag
from app.database.schemas import BeatmapsetTagSchema
from app.exceptions import NotFound
from app.spec import get_include_schema


@api_query(ModelClass.BEATMAPSET_TAG, many=True)
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    beatmapset_tags = await db.get_many(
        BeatmapsetTag,
        **kwargs
    )

    if not beatmapset_tags:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=beatmapset_tags[0],
        include_schema=get_include_schema(ModelClass.BEATMAPSET_TAG),
        request_include=kwargs.get("_include")
    )

    beatmapset_tags_data = [
        BeatmapsetTagSchema.model_validate(beatmapset_tag).model_dump(include=include)
        for beatmapset_tag in beatmapset_tags
    ]

    return beatmapset_tags_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.BEATMAPSET_TAG)
async def get(beatmapset_tag_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    beatmapset_tag = await db.get(
        BeatmapsetTag,
        id=beatmapset_tag_id,
        **kwargs
    )

    if not beatmapset_tag:
        raise NotFound(f"BeatmapsetTag with id '{beatmapset_tag_id}' not found")

    include = build_pydantic_include(
        obj=beatmapset_tag,
        include_schema=get_include_schema(ModelClass.BEATMAPSET_TAG),
        request_include=kwargs.get("_include")
    )

    beatmapset_tag_data = BeatmapsetTagSchema.model_validate(beatmapset_tag).model_dump(include=include)

    return beatmapset_tag_data, 200, {"Content-Type": "application/json"}
