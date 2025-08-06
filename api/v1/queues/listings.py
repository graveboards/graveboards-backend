from connexion import request

from api.utils import prime_query_kwargs
from app.database import PostgresqlDB
from app.database.schemas import QueueListingSchema, QueueSchema
from app.security import ownership_authorization

_LOADING_OPTIONS = {
    "queue": {
        "options": {
            "user_profile": False,
            "manager_profiles": False,
            "requests": False,
            "managers": False
        }
    },
    "request_listings": False,
}


@ownership_authorization()
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    queue_listings = await db.get_queue_listings(
        _loading_options=_LOADING_OPTIONS,
        **kwargs
    )
    queue_listings_data = [
        QueueListingSchema.model_validate(queue_listing).model_dump(
            context={
                "exclusions": {
                    QueueSchema: {"user_profile", "manager_profiles", "requests", "managers"},
                    QueueListingSchema: {"request_listings"}
                }
            }
        )
        for queue_listing in queue_listings
    ]

    return queue_listings_data, 200
