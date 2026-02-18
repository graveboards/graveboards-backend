from enum import Enum, IntEnum, auto
from typing import Callable

from sqlalchemy import asc, desc


class SortingOrder(Enum):
    """Sort direction for ordered queries.

    Maps public-facing sort identifiers to ORM ascending or descending functions.
    """
    ASCENDING = "asc"
    DESCENDING = "desc"

    @property
    def sort_func(self) -> Callable:
        """Return the ORM sort function corresponding to the order."""
        return asc if self is SortingOrder.ASCENDING else desc

    @classmethod
    def from_name(cls, name: str) -> "SortingOrder":
        """Resolve a sorting order from its string name.

        Args:
            name:
                Case-insensitive sort direction.

        Returns:
            Matching ``SortingOrder``.

        Raises:
            ValueError:
                If no matching sorting order exists.
        """
        for member_name, member in cls.__members__.items():
            if name.upper() == member_name:
                return member

        raise ValueError(f"No SortingOrder exists by the name of '{name}'")


SortingOrderId = IntEnum("SortingOrderId", {field.name: auto() for field in SortingOrder})
"""Compact integer identifiers for ``SortingOrder``.

Used for deterministic binary serialization of sort direction.
"""
