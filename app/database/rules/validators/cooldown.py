from __future__ import annotations

from datetime import datetime, timezone

from connexion.exceptions import Forbidden

from app.database.models import Queue
from app.redis import Namespace
from app.database.rules.base import RestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.schemas.rule import CooldownConfig


def _is_target_match(config: dict, user_id: int) -> bool:
    target = config.get("target")
    if target is None or not target:
        return True
    return user_id in target


class CooldownRestriction(RestrictionBase):
    type = "cooldown"
    config_schema = CooldownConfig

    async def _check(self, context: ExecutionContext) -> None:
        config = context.config
        cooldown_seconds = config.get("cooldown_seconds")
        scope = config.get("scope", "user")

        if not _is_target_match(config, context.user_id):
            return

        if scope != "user":
            return

        redis_key = Namespace.QUEUE_RESTRICTION_COOLDOWN.hash_name(
            f"{context.queue_id}:{context.user_id}"
        )

        last_request_ts = await context.redis.get(redis_key)

        if last_request_ts is not None:
            last_request_time = datetime.fromtimestamp(
                int(last_request_ts), tz=timezone.utc
            )
            elapsed = (datetime.now(timezone.utc) - last_request_time).total_seconds()

            if elapsed < cooldown_seconds:
                remaining = cooldown_seconds - elapsed
                remaining_hours = int(remaining // 3600)
                remaining_minutes = int((remaining % 3600) // 60)

                queue = await context.db.get(Queue, id=context.queue_id)
                queue_name = queue.name if queue else f"Queue {context.queue_id}"

                time_parts = []
                if remaining_hours > 0:
                    time_parts.append(f"{remaining_hours}h")
                if remaining_minutes > 0 or not time_parts:
                    time_parts.append(f"{remaining_minutes}m")

                raise Forbidden(
                    detail=(
                        f"You must wait before submitting another request to "
                        f"'{queue_name}' (queue {context.queue_id}): "
                        f"{remaining:.0f}s remaining ({', '.join(time_parts)})."
                    )
                )

        await context.redis.set(redis_key, int(datetime.now(timezone.utc).timestamp()))
        await context.redis.expire(redis_key, cooldown_seconds)
