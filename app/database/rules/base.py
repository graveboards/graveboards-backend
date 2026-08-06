"""Base classes and shared lifecycle for all rule restrictions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from app.database.rules.exceptions import RuleViolationError

if TYPE_CHECKING:
    import builtins

    from pydantic import BaseModel

    from app.database.rules.context import ExecutionContext


class RestrictionBase(ABC):
    """Base class for a rule restriction with a validation lifecycle.

    Subclasses declare their rule type, config schema and supported config versions,
    implement ``_check`` (or ``check_beatmap``/``check_database`` via the
    beatmap/database subclasses), and may override ``reserve``/``rollback`` for
    stateful rules.
    """

    type: str = ""
    config_schema: builtins.type[BaseModel] | None = None
    supported_versions: ClassVar[set[str]] = {"1.0"}

    async def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate the rule config against this rule's schema, if any.

        Returns the validated config with ``None`` fields omitted, or the raw
        config unchanged when no schema is configured.
        """
        if self.config_schema:
            validated = self.config_schema(**config)
            return dict(validated.model_dump(exclude_none=True))
        return config

    async def check(self, context: ExecutionContext) -> None:
        """Require a config and run this rule's ``_check`` against a context."""
        if not context.config:
            raise RuleViolationError(
                self.type,
                f"Missing configuration for rule type '{self.type}'",
            )
        await self._check(context)

    @abstractmethod
    async def _check(self, context: ExecutionContext) -> None: ...

    async def reserve(self, _context: ExecutionContext, _config: dict[str, Any]) -> str | None:
        """Atomically reserve any stateful side effect this rule consumes.

        Stateless rules do nothing. Stateful rules (rate limit, cooldown) override this
        to consume their Redis state only after all synchronous checks pass, returning a
        rollback token, and raise ``Forbidden`` if the reservation is not allowed.

        Returns:
        -------
            A rollback token, or ``None`` if the rule does not apply / has no state.
        """
        return None

    async def rollback(self, _context: ExecutionContext, _token: str) -> None:
        """Undo a reservation previously returned by :meth:`reserve`."""
        return


class BeatmapRestrictionBase(RestrictionBase):
    """Base class for restrictions evaluated against beatmapset metadata."""

    async def _check(self, context: ExecutionContext) -> None:
        if not context.beatmapset:
            raise RuleViolationError(
                self.type,
                "Beatmapset metadata not available",
            )
        await self.check_beatmap(context)

    @abstractmethod
    async def check_beatmap(self, context: ExecutionContext) -> None:
        """Evaluate this rule against the context's beatmapset metadata."""


class DatabaseRestrictionBase(RestrictionBase):
    """Base class for restrictions that require osu! API / database access."""

    async def _check(self, context: ExecutionContext) -> None:
        if not context.osu_client:
            raise RuleViolationError(
                self.type,
                "This rule requires osu! API access (Phase 2 only)",
            )
        await self.check_database(context)

    @abstractmethod
    async def check_database(self, context: ExecutionContext) -> None:
        """Evaluate this rule against live osu! API / database data."""
