from connexion import request

from api.utils import prime_query_kwargs
from app.database import PostgresqlDB
from app.database.models import Profile, ModelClass
from app.database.schemas import ProfileSchema


async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    profiles = await db.get_many(
        Profile,
        **kwargs
    )
    profiles_data = [
        ProfileSchema.model_validate(profile).model_dump()
        for profile in profiles
    ]

    return profiles_data, 200


async def get(user_id: int):
    db: PostgresqlDB = request.state.db

    profile = await db.get(
        Profile,
        user_id=user_id,
    )

    if not profile:
        return {"message": f"Profile with user_id '{user_id}' not found"}, 404

    profile_data = ProfileSchema.model_validate(profile).model_dump()

    return profile_data, 200
