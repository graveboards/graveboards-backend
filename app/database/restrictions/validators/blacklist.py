from __future__ import annotations

from connexion.exceptions import Forbidden

from app.database.models import Queue
from app.redis import Namespace
from app.database.restrictions.base import RestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.schemas.restriction import BlacklistConfig


def _is_target_match(config: dict, user_id: int) -> bool:
    target = config.get("target")
    if target is None or not target:
        return True
    return user_id in target


class BlacklistRestriction(RestrictionBase):
    restriction_type = "blacklist"
    config_schema = BlacklistConfig

    async def _check(self, context: ExecutionContext) -> None:
        config = context.config
        scope = config.get("scope", "user")
        target = config.get("target", [])

        if not target:
            return

        if scope == "user" and context.user_id in target:
            queue = await context.db.get(Queue, id=context.queue_id)
            queue_name = queue.name if queue else f"Queue {context.queue_id}"

            raise Forbidden(
                detail=(
                    f"You are not allowed to submit requests to "
                    f"'{queue_name}' (queue {context.queue_id})."
                )
            )
