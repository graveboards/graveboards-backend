import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import QueueRule
from app.exceptions import Conflict, BadRequest
from .decorators import session_manager

RULE_UPDATABLE_FIELDS = frozenset({"is_active", "is_public", "config", "version"})


def _validate_rule_version(rule_type: str, version: str) -> None:
    """Reject an unsupported version for a rule type at write time.

    An apparently active rule stored with an unsupported version is silently
    skipped by both phase runners, so it must never be persisted in the first place.

    Raises:
        BadRequest:
            If the version is not supported by the rule type's validator.
    """
    from app.database.rules.registry import get_supported_versions

    supported = get_supported_versions(rule_type)
    if supported is not None and version not in supported:
        raise BadRequest(
            f"Unsupported version '{version}' for rule type '{rule_type}'. "
            f"Supported: {', '.join(sorted(supported))}"
        )


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
            _validate_rule_version(data["type"], version)
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
                is_public=data.get("is_public", True),
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
        """Update a specific rule by ID.

        Only whitelisted fields may change. A supplied config is revalidated against
        the rule's immutable type, a supplied version is checked against the type's
        supported versions, and the resulting (type, version, config) fingerprint is
        rejected if it would duplicate another rule in the same queue.

        Raises:
            BadRequest:
                If a non-updatable field is supplied, or config/version is invalid.
            Conflict:
                If the update would duplicate an existing rule in the queue.
        """
        from app.database.schemas.rule import validate_rule_config
        from app.database.rules.registry import get_supported_versions

        disallowed = set(updates) - RULE_UPDATABLE_FIELDS
        if disallowed:
            raise BadRequest(
                f"These rule fields cannot be updated: {', '.join(sorted(disallowed))}"
            )

        stmt = select(QueueRule).where(
            QueueRule.id == rule_id,
            QueueRule.queue_id == queue_id,
        )
        result = await session.execute(stmt)
        rule = result.scalars().first()

        if not rule:
            return None

        updates = dict(updates)

        # Revalidate config against the rule's immutable type.
        if updates.get("config") is not None:
            try:
                updates["config"] = validate_rule_config(rule.type, updates["config"])
            except Exception as e:
                raise BadRequest(f"Invalid config for rule type '{rule.type}': {e}")

        # Validate version against the type's supported versions.
        if updates.get("version") is not None:
            supported = get_supported_versions(rule.type)
            if supported is not None and updates["version"] not in supported:
                raise BadRequest(
                    f"Unsupported version '{updates['version']}' for rule type "
                    f"'{rule.type}'. Supported: {', '.join(sorted(supported))}"
                )

        # Reject a patch that would duplicate another rule in the same queue.
        final_version = updates.get("version") or rule.version
        final_config = updates["config"] if updates.get("config") is not None else rule.config
        new_key = (rule.type, final_version, _normalize_config(final_config))

        for other in await self.get_rules(queue_id, session=session):
            if other.id == rule_id:
                continue
            other_key = (other.type, other.version, _normalize_config(other.config))
            if other_key == new_key:
                raise Conflict(
                    f"This update would duplicate an existing {rule.type} rule with the "
                    f"same configuration in this queue."
                )

        for key, value in updates.items():
            if value is not None and key in RULE_UPDATABLE_FIELDS:
                setattr(rule, key, value)

        await session.flush()
        await session.refresh(rule)

        return rule

    @session_manager()
    async def get_rule(
        self,
        queue_id: int,
        rule_id: int,
        session: AsyncSession = None,
    ) -> QueueRule | None:
        """Fetch a single rule by ID, scoped to a queue."""
        stmt = select(QueueRule).where(
            QueueRule.id == rule_id,
            QueueRule.queue_id == queue_id,
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @session_manager()
    async def create_rule(
        self,
        queue_id: int,
        rule_data: dict,
        session: AsyncSession = None,
    ) -> QueueRule:
        """Create a single rule and append it to the queue's existing rules."""
        _validate_rule_version(rule_data["type"], rule_data.get("version", "1.0"))

        existing = await self.get_rules(queue_id, session=session)
        new_key = (
            rule_data["type"],
            rule_data.get("version", "1.0"),
            _normalize_config(rule_data.get("config", {})),
        )
        for existing_rule in existing:
            existing_key = (
                existing_rule.type,
                existing_rule.version,
                _normalize_config(existing_rule.config),
            )
            if existing_key == new_key:
                raise Conflict(
                    f"Duplicate rule: {rule_data['type']} v{rule_data.get('version', '1.0')} with the "
                    f"same configuration has already been added."
                )

        rule = QueueRule(
            queue_id=queue_id,
            type=rule_data["type"],
            config=rule_data.get("config", {}),
            is_active=rule_data.get("is_active", True),
            is_public=rule_data.get("is_public", True),
            version=rule_data.get("version", "1.0"),
        )
        session.add(rule)
        await session.flush()
        await session.refresh(rule)
        return rule

    @session_manager()
    async def delete_rule(
        self,
        rule_id: int,
        queue_id: int,
        session: AsyncSession = None,
    ) -> QueueRule | None:
        """Delete a single rule by ID, scoped to a queue."""
        stmt = select(QueueRule).where(
            QueueRule.id == rule_id,
            QueueRule.queue_id == queue_id,
        )
        result = await session.execute(stmt)
        rule = result.scalars().first()

        if not rule:
            return None

        await session.delete(rule)
        await session.flush()
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
