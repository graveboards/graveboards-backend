from connexion.exceptions import Forbidden

from app.database import PostgresqlDB
from app.database.models import Queue
from app.redis import RedisClient
from app.database.restrictions.base import RestrictionBase


def _is_target_match(config: dict, user_id: int) -> bool:
    target = config.get("target")
    if target is None or not target:
        return True
    return user_id in target


class BlacklistRestriction(RestrictionBase):
    restriction_type = "blacklist"

    async def check(
        self,
        queue_id: int,
        user_id: int,
        db: PostgresqlDB,
        redis: RedisClient,  # noqa: ARG002
        config: dict,
    ) -> None:
        scope = config.get("scope", "user")
        target = config.get("target", [])

        if not target:
            return

        if scope == "user" and user_id in target:
            queue = await db.get(Queue, id=queue_id)
            queue_name = queue.name if queue else f"Queue {queue_id}"

            raise Forbidden(
                detail=(
                    f"You are not allowed to submit requests to "
                    f"'{queue_name}' (queue {queue_id})."
                )
            )
