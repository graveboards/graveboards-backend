from connexion import request

from api.decorators import api_query
from api.utils import build_pydantic_include, bleach_body
from app.database import PostgresqlDB
from app.database.models import User, ModelClass
from app.database.schemas import UserSchema
from app.database.enums import RoleName
from app.exceptions import NotFound, Conflict
from app.security import role_authorization
from app.security.overrides import matching_user_id_override
from app.spec import get_include_schema


@api_query(ModelClass.USER)
@role_authorization(RoleName.ADMIN)
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    users = await db.get_many(
        User,
        **kwargs
    )

    if not users:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=users[0],
        include_schema=get_include_schema(ModelClass.USER),
        request_include=kwargs.get("_include")
    )

    users_data = [
        UserSchema.model_validate(user).model_dump(include=include)
        for user in users
    ]

    return users_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.USER)
@role_authorization(RoleName.ADMIN, override=matching_user_id_override)
async def get(user_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    user = await db.get(
        User,
        id=user_id,
        **kwargs
    )

    if not user:
        raise NotFound(f"User with ID '{user_id}' not found")

    include = build_pydantic_include(
        obj=user,
        include_schema=get_include_schema(ModelClass.USER),
        request_include=kwargs.get("_include")
    )

    user_data = UserSchema.model_validate(user).model_dump(include=include)

    return user_data, 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN)
async def post(body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    if await db.get(User, id=body["user_id"]):
        raise Conflict(f"The user with ID '{body["user_id"]}' already exists")

    body = bleach_body(
        body,
        whitelisted_keys={"user_id"}
    )

    await db.add(User, **body)

    return {"message": "User added successfully!"}, 201, {"Content-Type": "application/json"}
