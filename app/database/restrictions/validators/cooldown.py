from datetime import datetime, timezone

from connexion.exceptions import Forbidden

from app.database import PostgresqlDB
from app.database.models import Queue
from app.redis import RedisClient, Namespace
from app.database.restrictions.base import RestrictionBase


def _is_target_match(config: dict, user_id: int) -> bool:
    target = config.get("target")
    if target is None or not target:
        return True
    return user_id in target


class CooldownRestriction(RestrictionBase):
    restriction_type = "cooldown"

    async def check(
        self,
        queue_id: int,
        user_id: int,
        db: PostgresqlDB,
        redis: RedisClient,
        config: dict,
    ) -> None:
        cooldown_seconds = config.get("cooldown_seconds")
        scope = config.get("scope", "user")

        if not _is_target_match(config, user_id):
            return

        if scope != "user":
            return

        redis_key = Namespace.QUEUE_RESTRICTION_COOLDOWN.hash_name(
            f"{queue_id}:{user_id}"
        )

        last_request_ts = await redis.get(redis_key)

        if last_request_ts is not None:
            last_request_time = datetime.fromtimestamp(
                int(last_request_ts), tz=timezone.utc
            )
            elapsed = (datetime.now(timezone.utc) - last_request_time).total_seconds()

            if elapsed < cooldown_seconds:
                remaining = cooldown_seconds - elapsed
                remaining_hours = int(remaining // 3600)
                remaining_minutes = int((remaining % 3600) // 60)

                queue = await db.get(Queue, id=queue_id)
                queue_name = queue.name if queue else f"Queue {queue_id}"

                time_parts = []
                if remaining_hours > 0:
                    time_parts.append(f"{remaining_hours}h")
                if remaining_minutes > 0 or not time_parts:
                    time_parts.append(f"{remaining_minutes}m")

                raise Forbidden(
                    detail=(
                        f"You must wait before submitting another request to "
                        f"'{queue_name}' (queue {queue_id}): "
                        f"{remaining:.0f}s remaining ({', '.join(time_parts)})."
                    )
                )

        await redis.set(redis_key, int(datetime.now(timezone.utc).timestamp()))
        await redis.expire(redis_key, cooldown_seconds)
