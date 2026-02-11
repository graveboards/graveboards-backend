from connexion import request

from api.utils import prime_query_kwargs
from api.utils import build_pydantic_include
from app.database import PostgresqlDB
from app.database.models import Profile, ModelClass
from app.database.schemas import ProfileSchema
from app.spec import get_include_schema


async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    profiles = await db.get_many(
        Profile,
        **kwargs
    )

    if not profiles:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=profiles[0],
        include_schema=get_include_schema(ModelClass.PROFILE),
        request_include=kwargs.get("_include")
    )

    profiles_data = [
        ProfileSchema.model_validate(profile).model_dump(include=include)
        for profile in profiles
    ]

    return profiles_data, 200


async def get(user_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    profile = await db.get(
        Profile,
        user_id=user_id,
        **kwargs
    )

    if not profile:
        return {"message": f"Profile with user_id '{user_id}' not found"}, 404

    include = build_pydantic_include(
        obj=profile,
        include_schema=get_include_schema(ModelClass.PROFILE),
        request_include=kwargs.get("_include")
    )

    return profile_data, 200
    profile_data = ProfileSchema.model_validate(profile).model_dump(include=include)

