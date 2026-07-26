from __future__ import annotations

from datetime import UTC, datetime

from connexion.exceptions import Forbidden

from app.database.models import Queue
from app.database.rules.base import RestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.fingerprint import config_fingerprint
from app.database.schemas.rule import CooldownConfig
from app.redis_client import Namespace


def _is_target_match(config: dict, user_id: int) -> bool:
    target = config.get("target")
    if target is None or not target:
        return True
    return user_id in target


class CooldownRestriction(RestrictionBase):
    type = "cooldown"
    config_schema = CooldownConfig

    def _applies(self, config: dict, user_id: int) -> bool:
        return _is_target_match(config, user_id) and config.get("scope", "user") == "user"

    def _redis_key(self, context: ExecutionContext, config: dict) -> str:
        return Namespace.QUEUE_RULE_COOLDOWN.hash_name(
            f"{context.queue_id}:{context.user_id}:{config_fingerprint(config)}"
        )

    def _remaining_seconds(self, last_request_ts: float | int, cooldown_seconds: int) -> float:
        last_request_time = datetime.fromtimestamp(int(last_request_ts), tz=UTC)
        elapsed = (datetime.now(UTC) - last_request_time).total_seconds()
        return cooldown_seconds - elapsed

    async def _cooldown_error(self, context: ExecutionContext, remaining: float) -> Forbidden:
        remaining = max(remaining, 0)
        remaining_hours = int(remaining // 3600)
        remaining_minutes = int((remaining % 3600) // 60)

        if context.db is None:
            queue_name = f"Queue {context.queue_id}"
        else:
            queue = await context.db.get(Queue, id=context.queue_id)
            queue_name = queue.name if queue else f"Queue {context.queue_id}"

        time_parts = []
        if remaining_hours > 0:
            time_parts.append(f"{remaining_hours}h")
        if remaining_minutes > 0 or not time_parts:
            time_parts.append(f"{remaining_minutes}m")

        return Forbidden(
            detail=(
                f"You must wait before submitting another request to "
                f"'{queue_name}' (queue {context.queue_id}): "
                f"{remaining:.0f}s remaining ({', '.join(time_parts)})."
            )
        )

    async def _check(self, context: ExecutionContext) -> None:
        config = context.config

        if not self._applies(config, context.user_id):
            return

        if context.redis is None:
            return

        cooldown_seconds = config.get("cooldown_seconds")
        redis_key = self._redis_key(context, config)

        last_request_ts = await context.redis.get(redis_key)
        if last_request_ts is not None and cooldown_seconds is not None:
            remaining = self._remaining_seconds(int(last_request_ts), cooldown_seconds)
            if remaining > 0:
                raise await self._cooldown_error(context, remaining)

    async def reserve(self, context: ExecutionContext, config: dict) -> str | None:
        if not self._applies(config, context.user_id):
            return None

        if context.redis is None:
            return None

        cooldown_seconds = config.get("cooldown_seconds")
        redis_key = self._redis_key(context, config)
        now_ts = int(datetime.now(UTC).timestamp())

        was_set = await context.redis.set(redis_key, now_ts, nx=True, ex=cooldown_seconds)
        if not was_set:
            last_request_ts = await context.redis.get(redis_key)
            if cooldown_seconds is None:
                raise await self._cooldown_error(context, 0.0)

            if last_request_ts is not None:
                remaining = self._remaining_seconds(int(last_request_ts), cooldown_seconds)
            else:
                remaining = float(cooldown_seconds)

            raise await self._cooldown_error(context, remaining)

        return redis_key

    async def rollback(self, context: ExecutionContext, token: str) -> None:
        if context.redis is None:
            return
        await context.redis.delete(token)
