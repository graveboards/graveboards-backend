from connexion import request

from api.utils import pop_auth_info
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

    pop_auth_info(kwargs)

    se = SearchEngine()

    async with db.session() as session:
        try:
            results_generator = se.search(session, **kwargs)
        except (ValueError, TypeError) as e:
            return {"message": str(e)}, 400

        try:
            page = await anext(results_generator)
        except StopAsyncIteration:
            return [], 200

        context = {
            "exclusions": {
                BeatmapSnapshotSchema: {"beatmapset_snapshots", "leaderboard"}
            }
        }

        page_data = [BeatmapsetListingSchema.model_validate(beatmapset_listing).model_dump(context=context) for beatmapset_listing in page]

    return page_data, 200
