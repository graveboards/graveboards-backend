"""Blacklist rule: reject blocked users for a queue."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from connexion.exceptions import Forbidden

from app.database.models import Queue
from app.database.rules.base import RestrictionBase
from app.database.schemas.rule import BlacklistConfig

if TYPE_CHECKING:
    from app.database.rules.context import ExecutionContext


def _is_target_match(config: dict[str, Any], user_id: int) -> bool:
    target = config.get("target")
    if target is None or not target:
        return True
    return user_id in target


class BlacklistRestriction(RestrictionBase):
    """Reject requests from a config-scoped list of blocked user ids."""

    type = "blacklist"
    config_schema = BlacklistConfig

    @override
    async def _check(self, context: ExecutionContext) -> None:
        config = context.config
        scope = config.get("scope", "user")
        target = config.get("target", [])

        if not target:
            return

        if scope == "user" and context.user_id in target:
            if context.db is None:
                queue_name = f"Queue {context.queue_id}"
            else:
                queue = await context.db.get(Queue, id=context.queue_id)
                queue_name = queue.name if queue else f"Queue {context.queue_id}"

            raise Forbidden(
                detail=(
                    f"You are not allowed to submit requests to "
                    f"'{queue_name}' (queue {context.queue_id})."
                )
            )
