import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import QueueRestriction
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


class RestrictionCRUD:
    @session_manager()
    async def get_restrictions(
        self,
        queue_id: int,
        session: AsyncSession = None,
        only_active: bool = False,
    ) -> list[QueueRestriction]:
        """Fetch all restrictions for a queue, optionally filtered by active status."""
        stmt = select(QueueRestriction).where(QueueRestriction.queue_id == queue_id)

        if only_active:
            stmt = stmt.where(QueueRestriction.is_active.is_(True))

        stmt = stmt.order_by(QueueRestriction.id.asc())

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @session_manager()
    async def upsert_restrictions(
        self,
        queue_id: int,
        restrictions_data: list[dict],
        session: AsyncSession = None,
    ) -> list[QueueRestriction]:
        """Replace all restrictions for a queue with the provided list.

        Deletes existing restrictions and creates new ones. If restrictions_data is
        empty or None, all existing restrictions are deleted.

        Raises:
            Conflict:
                If the input list contains fully duplicate rules (same restriction_type
                and same config).
        """
        if not restrictions_data:
            await self._delete_all_for_queue(queue_id, session=session)
            return []

        seen = set()
        for data in restrictions_data:
            config = data.get("config", {})
            key = (data["restriction_type"], _normalize_config(config))
            if key in seen:
                raise Conflict(
                    f"Duplicate restriction rule: {data['restriction_type']} with the "
                    f"same configuration has already been added."
                )
            seen.add(key)

        existing = await self.get_restrictions(queue_id, session=session)

        for item in existing:
            await session.delete(item)

        await session.flush()

        created = []
        for data in restrictions_data:
            restriction = QueueRestriction(
                queue_id=queue_id,
                restriction_type=data["restriction_type"],
                config=data.get("config", {}),
                is_active=data.get("is_active", True),
            )
            session.add(restriction)
            created.append(restriction)

        await session.flush()

        for item in created:
            await session.refresh(item)

        return created

    @session_manager()
    async def update_restriction(
        self,
        restriction_id: int,
        queue_id: int,
        updates: dict,
        session: AsyncSession = None,
    ) -> QueueRestriction | None:
        """Update a specific restriction by ID."""
        stmt = select(QueueRestriction).where(
            QueueRestriction.id == restriction_id,
            QueueRestriction.queue_id == queue_id,
        )
        result = await session.execute(stmt)
        restriction = result.scalars().first()

        if not restriction:
            return None

        for key, value in updates.items():
            if value is not None and hasattr(restriction, key):
                setattr(restriction, key, value)

        await session.flush()
        await session.refresh(restriction)

        return restriction

    async def _delete_all_for_queue(
        self,
        queue_id: int,
        session: AsyncSession,
    ) -> None:
        stmt = select(QueueRestriction).where(QueueRestriction.queue_id == queue_id)
        result = await session.execute(stmt)
        for item in result.scalars().all():
            await session.delete(item)
        await session.flush()
