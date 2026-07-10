import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import QueueRule
from app.exceptions import Conflict
from .decorators import session_manager


def _normalize_config(config: dict) -> str:
    """Normalize a config dict to a canonical string for comparison.

    Sorts keys recursively and serializes to JSON so that two configs with the same
    data produce identical strings regardless of key order.
    """
    def _sort(obj):
        if isinstance(obj, dict):
            return {k: _sort(v) for k, v in sorted(obj.items())}
        if isinstance(obj, list):
            return sorted(_sort(item) for item in obj)
        return obj

    return json.dumps(_sort(config), sort_keys=True, default=str)


class RuleCRUD:
    @session_manager()
    async def get_rules(
        self,
        queue_id: int,
        session: AsyncSession = None,
        only_active: bool = False,
    ) -> list[QueueRule]:
        """Fetch all rules for a queue, optionally filtered by active status."""
        stmt = select(QueueRule).where(QueueRule.queue_id == queue_id)

        if only_active:
            stmt = stmt.where(QueueRule.is_active.is_(True))

        stmt = stmt.order_by(QueueRule.id.asc())

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @session_manager()
    async def upsert_rules(
        self,
        queue_id: int,
        rules_data: list[dict],
        session: AsyncSession = None,
    ) -> list[QueueRule]:
        """Replace all rules for a queue with the provided list.

        Deletes existing rules and creates new ones. If rules_data is
        empty or None, all existing rules are deleted.

        Raises:
            Conflict:
                If the input list contains fully duplicate rules (same type
                and same config).
        """
        if not rules_data:
            await self._delete_all_for_rule(queue_id, session=session)
            return []

        seen = set()
        for data in rules_data:
            config = data.get("config", {})
            version = data.get("version", "1.0")
            key = (data["type"], version, _normalize_config(config))
            if key in seen:
                raise Conflict(
                    f"Duplicate rule: {data['type']} v{version} with the "
                    f"same configuration has already been added."
                )
            seen.add(key)

        existing = await self.get_rules(queue_id, session=session)

        for item in existing:
            await session.delete(item)

        await session.flush()

        created = []
        for data in rules_data:
            rule = QueueRule(
                queue_id=queue_id,
                type=data["type"],
                config=data.get("config", {}),
                is_active=data.get("is_active", True),
                version=data.get("version", "1.0"),
            )
            session.add(rule)
            created.append(rule)

        await session.flush()

        for item in created:
            await session.refresh(item)

        return created

    @session_manager()
    async def update_rule(
        self,
        rule_id: int,
        queue_id: int,
        updates: dict,
        session: AsyncSession = None,
    ) -> QueueRule | None:
        """Update a specific rule by ID."""
        stmt = select(QueueRule).where(
            QueueRule.id == rule_id,
            QueueRule.queue_id == queue_id,
        )
        result = await session.execute(stmt)
        rule = result.scalars().first()

        if not rule:
            return None

        for key, value in updates.items():
            if value is not None and hasattr(rule, key):
                setattr(rule, key, value)

        await session.flush()
        await session.refresh(rule)

        return rule

    async def _delete_all_for_rule(
        self,
        queue_id: int,
        session: AsyncSession,
    ) -> None:
        stmt = select(QueueRule).where(QueueRule.queue_id == queue_id)
        result = await session.execute(stmt)
        for item in result.scalars().all():
            await session.delete(item)
        await session.flush()
