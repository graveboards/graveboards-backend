from abc import ABC, abstractmethod
from typing import Any

from app.database import PostgresqlDB
from app.redis import RedisClient


class RestrictionBase(ABC):
    restriction_type: str = ""

    @abstractmethod
    async def check(
        self,
        queue_id: int,
        user_id: int,
        db: PostgresqlDB,
        redis: RedisClient,
        config: dict[str, Any],
    ) -> None:
        """Validate that the restriction is not violated.

        Args:
            queue_id:
                The queue the restriction applies to.
            user_id:
                The user submitting the request.
            db:
                Active database interface.
            redis:
                Active Redis client.
            config:
                The restriction configuration dict.

        Raises:
            Forbidden:
                If the restriction is violated.
        """
