from __future__ import annotations

import logging
from dataclasses import dataclass

from app.database.models import QueueRule
from app.database.rules.base import RestrictionBase
from app.database.rules.context import ExecutionContext

logger = logging.getLogger(__name__)

# Tier-1 rule types that consume Redis state. These are evaluated as pure eligibility
# checks during Phase 1 and only committed (reserved) after all synchronous checks and
# the request enqueue succeed - see reserve_stateful_rules.
STATEFUL_RULE_TYPES = frozenset({"rate_limit", "cooldown"})


@dataclass
class Reservation:
    validator: RestrictionBase
    token: str


async def reserve_stateful_rules(
    rules: list[QueueRule],
    context: ExecutionContext,
) -> list[Reservation]:
    """Atomically reserve state for every applicable stateful rule.

    Each reservation is atomic and per-rule. If any rule rejects
    the request (rate limit exceeded / cooldown active), every reservation already made
    for this request is rolled back before the rejection propagates, so a blocked
    request consumes no state.

    Args:
        rules:
            The queue's active rules (the same list evaluated in Phase 1).
        context:
            Execution context carrying the Redis client, DB, user and queue.

    Returns:
        The list of successful reservations, to be committed by the caller once the
        request is enqueued, or rolled back if the enqueue fails.

    Raises:
        connexion.exceptions.Forbidden:
            If a stateful rule blocks the request.
    """
    from app.database.rules.registry import get_validator

    reservations: list[Reservation] = []

    try:
        for rule in rules:
            if not rule.is_active or rule.type not in STATEFUL_RULE_TYPES:
                continue

            validator_cls = get_validator(rule.type)
            if validator_cls is None:
                continue

            if rule.version not in validator_cls.supported_versions:
                continue

            validator = validator_cls()
            token = await validator.reserve(context, rule.config or {})

            if token is not None:
                reservations.append(Reservation(validator, token))
    except Exception:
        await rollback_reservations(reservations, context)
        raise

    return reservations


async def rollback_reservations(
    reservations: list[Reservation],
    context: ExecutionContext,
) -> None:
    """Undo reservations, e.g. when enqueue/persistence fails after reserving."""
    for reservation in reservations:
        try:
            await reservation.validator.rollback(context, reservation.token)
        except Exception:
            logger.warning(
                "Failed to roll back stateful reservation (token=%s)",
                reservation.token,
            )
