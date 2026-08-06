"""Hashable wrapper for SQLAlchemy CTEs."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import CTE


class HashableCTE:
    """Make a CTE usable as a dict key or set member via its name."""

    def __init__(self, cte: CTE) -> None:
        self.cte = cte

    def __hash__(self) -> int:
        return hash(self.cte.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HashableCTE):
            return False

        return bool(self.cte.name == other.cte.name)
