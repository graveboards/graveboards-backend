from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from pydantic import BaseModel

from app.database.rules.exceptions import RuleViolationError

if TYPE_CHECKING:
    from app.database.rules.context import ExecutionContext


class RestrictionBase(ABC):
    type: str = ""
    config_schema: type[BaseModel] | None = None
    supported_versions: set[str] = {"1.0"}

    async def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        if self.config_schema:
            validated = self.config_schema(**config)
            return validated.model_dump(exclude_none=True)
        return config

    async def check(self, context: ExecutionContext) -> None:
        if not context.config:
            raise RuleViolationError(
                self.type,
                f"Missing configuration for rule type '{self.type}'",
            )
        await self._check(context)

    @abstractmethod
    async def _check(self, context: ExecutionContext) -> None:
        ...


class BeatmapRestrictionBase(RestrictionBase):
    async def _check(self, context: ExecutionContext) -> None:
        if not context.beatmapset:
            raise RuleViolationError(
                self.type,
                "Beatmapset metadata not available",
            )
        await self.check_beatmap(context)

    @abstractmethod
    async def check_beatmap(self, context: ExecutionContext) -> None:
        ...


class DatabaseRestrictionBase(RestrictionBase):
    async def _check(self, context: ExecutionContext) -> None:
        if not context.osu_client:
            raise RuleViolationError(
                self.type,
                "This rule requires osu! API access (Phase 2 only)",
            )
        await self.check_database(context)

    @abstractmethod
    async def check_database(self, context: ExecutionContext) -> None:
        ...
