"""Re-exports for the users v1 API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from api.decorators import api_query
from api.utils import bleach_body, build_pydantic_include
from app.database.enums import RoleName
from app.database.models import ModelClass, User

if TYPE_CHECKING:
    from starlette.requests import Request

    from api.http_types import APIResponse
    from app.database import PostgresqlDB
from app.database.schemas import UserSchema
from app.exceptions import Conflict, NotFound
from app.security import role_authorization
from app.security.overrides import matching_user_id_override
from app.spec import get_include_schema

from . import api_key

__all__ = ["api_key", "get", "post", "search"]


@role_authorization(RoleName.ADMIN)
@api_query(ModelClass.USER, many=True)
async def search(request: Request, **_kwargs: Any) -> APIResponse:
    """Search for users.

    Returns:
        Tuple of (users data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    users = await db.get_many(User, **_kwargs)

    if not users:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=users[0],
        include_schema=get_include_schema(ModelClass.USER),
        request_include=_kwargs.get("_include"),
    )

    users_data = [UserSchema.model_validate(user).model_dump(include=include) for user in users]

    return users_data, 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=matching_user_id_override)
@api_query(ModelClass.USER)
async def get(request: Request, user_id: int, **_kwargs: Any) -> APIResponse:
    """Get a single user by ID.

    Returns:
        Tuple of (user data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    user = await db.get(User, id=user_id, **_kwargs)

    if not user:
        raise NotFound(f"User with ID '{user_id}' not found")

    include = build_pydantic_include(
        obj=user,
        include_schema=get_include_schema(ModelClass.USER),
        request_include=_kwargs.get("_include"),
    )

    user_data = UserSchema.model_validate(user).model_dump(include=include)

    return user_data, 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN)
async def post(request: Request, body: dict, **_kwargs: Any) -> APIResponse:
    """Create a new user.

    Returns:
        Tuple of (message, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    user_id = body["id"]

    if await db.get(User, id=user_id):
        raise Conflict(f"The user with ID '{user_id}' already exists")

    body = bleach_body(body, whitelisted_keys={"id", "roles"})

    await db.add(User, **body)

    return {"message": "User added successfully!"}, 201, {"Content-Type": "application/json"}
