from __future__ import annotations

from datetime import datetime, timedelta, timezone

from connexion.exceptions import Forbidden

from app.database.models import Queue
from app.redis import Namespace
from app.database.rules.base import RestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.fingerprint import config_fingerprint
from app.database.schemas.rule import RateLimitConfig


def _truncate_to_period(now: datetime, period: str) -> int:
    if period == "day":
        truncated = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        truncated = now - timedelta(days=now.weekday())
        truncated = truncated.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        truncated = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        truncated = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            period_seconds = int(period)
            if period_seconds <= 0:
                raise ValueError
            epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
            bucket = int((now - epoch).total_seconds() // period_seconds)
            return bucket * period_seconds
        except (ValueError, TypeError):
            raise ValueError(f"Invalid period: {period}") from None

    return int(truncated.timestamp())


def _period_duration_seconds(period: str) -> int:
    if period == "day":
        return 86400
    elif period == "week":
        return 604800
    elif period == "month":
        return 2592000
    elif period == "year":
        return 31536000
    else:
        try:
            return int(period)
        except (ValueError, TypeError):
            return 604800


def _is_target_match(config: dict, user_id: int) -> bool:
    target = config.get("target")
    if target is None or not target:
        return True
    return user_id in target


class RateLimitRestriction(RestrictionBase):
    type = "rate_limit"
    config_schema = RateLimitConfig

    def _applies(self, config: dict, user_id: int) -> bool:
        return _is_target_match(config, user_id) and config.get("scope", "user") == "user"

    def _redis_key(self, context: ExecutionContext, config: dict) -> str:
        period = config.get("period", "week")
        period_bucket = _truncate_to_period(datetime.now(timezone.utc), period)
        return Namespace.QUEUE_RESTRICTION_RATE_LIMIT.hash_name(
            f"{context.queue_id}:{context.user_id}:{config_fingerprint(config)}:{period_bucket}"
        )

    async def _limit_error(self, context: ExecutionContext, config: dict) -> Forbidden:
        max_requests = config.get("max_requests")
        period = config.get("period", "week")
        queue = await context.db.get(Queue, id=context.queue_id)
        queue_name = queue.name if queue else f"Queue {context.queue_id}"

        return Forbidden(
            detail=(
                f"You have exceeded the rate limit for "
                f"'{queue_name}' (queue {context.queue_id}): max "
                f"{max_requests} request{'s' if max_requests != 1 else ''} "
                f"per {period}. Please try again in the next period."
            )
        )

    async def _check(self, context: ExecutionContext) -> None:
        config = context.config

        if not self._applies(config, context.user_id):
            return

        max_requests = config.get("max_requests")
        redis_key = self._redis_key(context, config)

        current = await context.redis.get(redis_key)
        count = int(current) if current is not None else 0

        if count >= max_requests:
            raise await self._limit_error(context, config)

    async def reserve(self, context: ExecutionContext, config: dict) -> str | None:
        if not self._applies(config, context.user_id):
            return None

        max_requests = config.get("max_requests")
        period = config.get("period", "week")
        redis_key = self._redis_key(context, config)

        current_count = await context.redis.incr(redis_key)
        if current_count == 1:
            await context.redis.expire(redis_key, _period_duration_seconds(period))

        if current_count > max_requests:
            await context.redis.decr(redis_key)
            raise await self._limit_error(context, config)

        return redis_key

    async def rollback(self, context: ExecutionContext, token: str) -> None:
        await context.redis.decr(token)
