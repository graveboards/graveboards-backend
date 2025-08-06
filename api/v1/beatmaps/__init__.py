from connexion import request

from api.utils import prime_query_kwargs
from app.database import PostgresqlDB
from app.database.schemas import BeatmapSchema
from . import snapshots

_LOADING_OPTIONS = {
    "snapshots": False,
    "leaderboards": False
}


async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    beatmaps = await db.get_beatmaps(
        _loading_options=_LOADING_OPTIONS,
        **kwargs
    )
    beatmaps_data = [
        BeatmapSchema.model_validate(beatmap).model_dump(
            exclude={"leaderboards", "snapshots"}
        )
        for beatmap in beatmaps
    ]

    return beatmaps_data, 200
