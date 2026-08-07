"""Re-exports for the profiles v1 API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from connexion import request

from api.decorators import api_query
from api.utils import build_pydantic_include
from app.database.models import ModelClass, Profile

if TYPE_CHECKING:
    from api.http_types import APIResponse
    from app.database import PostgresqlDB
from app.database.schemas import ProfileSchema
from app.exceptions import NotFound
from app.security import ownership_authorization
from app.spec import get_include_schema

__all__ = ["get", "search"]


@api_query(ModelClass.PROFILE, many=True)
async def search(**kwargs: Any) -> APIResponse:
    """Search for profiles.

    Returns:
        Tuple of (profiles data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    profiles = await db.get_many(Profile, **kwargs)

    if not profiles:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=profiles[0],
        include_schema=get_include_schema(ModelClass.PROFILE),
        request_include=kwargs.get("_include"),
    )

    profiles_data = [
        ProfileSchema.model_validate(profile).model_dump(include=include) for profile in profiles
    ]

    return profiles_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.PROFILE)
@ownership_authorization()
async def get(user_id: int, **kwargs: Any) -> APIResponse:
    """Get a single profile by user ID.

    Returns:
        Tuple of (profile data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    profile = await db.get(Profile, user_id=user_id, **kwargs)

    if not profile:
        raise NotFound(f"Profile with user_id '{user_id}' not found")

    include = build_pydantic_include(
        obj=profile,
        include_schema=get_include_schema(ModelClass.PROFILE),
        request_include=kwargs.get("_include"),
    )

    profile_data = ProfileSchema.model_validate(profile).model_dump(include=include)

    return profile_data, 200, {"Content-Type": "application/json"}
