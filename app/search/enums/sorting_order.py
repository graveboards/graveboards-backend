from collections.abc import Callable
from enum import Enum, IntEnum, auto
from typing import Any
from typing import cast as typing_cast

from sqlalchemy import asc, desc


class SortingOrder(Enum):
    """Sort direction for ordered queries.

    Maps public-facing sort identifiers to ORM ascending or descending functions.
    """

    ASCENDING = "asc"
    DESCENDING = "desc"

    @property
    def sort_func(self) -> Callable[..., Any]:
        """Return the ORM sort function corresponding to the order."""
        return typing_cast(Callable[..., Any], asc if self is SortingOrder.ASCENDING else desc)

    @classmethod
    def from_name(cls, name: str) -> SortingOrder:
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


_sorting_order_id_map: dict[str, int] = {field.name: auto() for field in SortingOrder}
SortingOrderId = IntEnum("SortingOrderId", _sorting_order_id_map)
"""Compact integer identifiers for ``SortingOrder``.

Used for deterministic binary serialization of sort direction.
"""
