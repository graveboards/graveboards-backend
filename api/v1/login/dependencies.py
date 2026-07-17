from typing import TYPE_CHECKING

from app.redis import RedisClient

if TYPE_CHECKING:
    from unittest.mock import AsyncMock


__all__ = ["get_redis_client", "RedisDependency"]


async def get_redis_client() -> RedisClient:
    """Get Redis client from request state.
    
    For testing, this can be overridden with a mock.
    """
    from connexion.context import request
    return request.state.rc


RedisDependency = None
