from connexion import request

from api.utils import prime_query_kwargs
from app.database import PostgresqlDB
from app.database.schemas import (
    RequestListingSchema,
    RequestSchema,
    BeatmapSnapshotSchema,
    QueueSchema,
    BeatmapsetSnapshotSchema
)
from app.security import ownership_authorization

_LOADING_OPTIONS = {
    "request": {
        "options": {
            "user_profile": False,
            "queue": {
                "options": {
                    "requests": False,
                    "managers": False,
                    "user_profile": False,
                    "manager_profiles": False
                }
            }
        }
    },
    "beatmapset_listing": {
        "options": {
            "beatmapset_snapshot": {
                "options": {
                    "beatmap_snapshots": {
                        "options": {
                            "beatmapset_snapshots": False,
                            "beatmap_tags": True,
                            "leaderboard": False,
                            "owner_profiles": False
                        }
                    },
                    "beatmapset_tags": True,
                    "user_profile": False
                }
            }
        }
    },
    "queue_listing": False
}


@ownership_authorization()
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    request_listings = await db.get_request_listings(
        _loading_options=_LOADING_OPTIONS,
        **kwargs
    )
    request_listings_data = [
        RequestListingSchema.model_validate(request_listing).model_dump(
            context={
                "exclusions": {
                    RequestSchema: {"user_profile"},
                    QueueSchema: {"user_profile", "manager_profiles", "requests", "managers"},
                    RequestListingSchema: {"queue_listing"},
                    BeatmapSnapshotSchema: {"owner_profiles", "beatmapset_snapshots", "leaderboard"},
                    BeatmapsetSnapshotSchema: {"user_profile"}
                }
            }
        )
        for request_listing in request_listings
    ]

    return request_listings_data, 200
