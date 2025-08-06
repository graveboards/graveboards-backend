from connexion import request

from api.utils import prime_query_kwargs
from app.database import PostgresqlDB
from app.database.schemas import BeatmapsetListingSchema, BeatmapSnapshotSchema

_LOADING_OPTIONS = {
    "beatmapset_snapshot": {
        "options": {
            "beatmap_snapshots": {
                "options": {
                    "owner_profiles": True,
                    "beatmapset_snapshots": False,
                    "leaderboard": False
                }
            },
            "beatmapset_tags": True,
            "user_profile": True
        }
    }
}


async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    beatmapset_listings = await db.get_beatmapset_listings(
        _loading_options=_LOADING_OPTIONS,
        **kwargs
    )
    beatmapset_listings_data = [
        BeatmapsetListingSchema.model_validate(beatmapset_listing).model_dump(
            context={
                "exclusions": {
                    BeatmapSnapshotSchema: {"beatmapset_snapshots", "leaderboard"}
                }
            }
        )
        for beatmapset_listing in beatmapset_listings
    ]

    return beatmapset_listings_data, 200
