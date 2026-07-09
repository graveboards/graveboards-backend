from __future__ import annotations

from datetime import datetime, timedelta, timezone

from connexion.exceptions import Forbidden

from app.database.models import Queue
from app.redis import Namespace
from app.database.restrictions.base import RestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.schemas.restriction import RateLimitConfig


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
    restriction_type = "rate_limit"
    config_schema = RateLimitConfig

    async def _check(self, context: ExecutionContext) -> None:
        config = context.config
        max_requests = config.get("max_requests")
        period = config.get("period", "week")
        scope = config.get("scope", "user")

        if not _is_target_match(config, context.user_id):
            return

        if scope != "user":
            return

        period_bucket = _truncate_to_period(datetime.now(timezone.utc), period)
        redis_key = Namespace.QUEUE_RESTRICTION_RATE_LIMIT.hash_name(
            f"{context.queue_id}:{context.user_id}:{period_bucket}"
        )

        current_count = await context.redis.incr(redis_key)
        if current_count == 1:
            duration = _period_duration_seconds(period)
            await context.redis.expire(redis_key, duration)

        if current_count > max_requests:
            queue = await context.db.get(Queue, id=context.queue_id)
            queue_name = queue.name if queue else f"Queue {context.queue_id}"

            raise Forbidden(
                detail=(
                    f"You have exceeded the rate limit for "
                    f"'{queue_name}' (queue {context.queue_id}): max "
                    f"{max_requests} request{'s' if max_requests != 1 else ''} "
                    f"per {period}. Please try again in the next period."
                )
            )
