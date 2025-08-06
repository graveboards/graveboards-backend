from connexion import request

from api.utils import prime_query_kwargs
from app.database import PostgresqlDB
from app.database.schemas import UserSchema
from app.database.enums import RoleName
from app.security import role_authorization
from app.security.overrides import matching_user_id_override

_LOADING_OPTIONS = {
    "profile": True,
    "roles": True,
    "scores": False,
    "tokens": False,
    "queues": False,
    "requests": False,
    "beatmapsets": False
}


@role_authorization(RoleName.ADMIN)
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    users = await db.get_users(
        _loading_options=_LOADING_OPTIONS,
        **kwargs
    )
    users_data = [
        UserSchema.model_validate(user).model_dump(
            exclude={"scores", "tokens", "queues", "requests", "beatmaps", "beatmapsets"}
        )
        for user in users
    ]

    return users_data, 200


@role_authorization(RoleName.ADMIN, override=matching_user_id_override)
async def get(user_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    user = await db.get_user(
        id=user_id,
        _loading_options=_LOADING_OPTIONS
    )

    if not user:
        return {"message": f"User with ID '{user_id}' not found"}, 404

    user_data = UserSchema.model_validate(user).model_dump(
        exclude={"scores", "tokens", "queues", "requests", "beatmaps", "beatmapsets"}
    )

    return user_data, 200


@role_authorization(RoleName.ADMIN)
async def post(body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    user_id = body["user_id"]

    if await db.get_user(id=user_id):
        return {"message": f"The user with ID '{user_id}' already exists"}, 409

    await db.add_user(id=user_id)

    return {"message": "User added successfully!"}, 201
