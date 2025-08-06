from enum import Enum, IntEnum, auto
from typing import Callable

from sqlalchemy import asc, desc


class SortingOrder(Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"

    @property
    def sort_func(self) -> Callable:
        return asc if self is SortingOrder.ASCENDING else desc

    @classmethod
    def from_name(cls, name: str) -> "SortingOrder":
        for member_name, member in cls.__members__.items():
            if name.upper() == member_name:
                return member

        raise ValueError(f"No SortingOrder exists by the name of '{name}'")


SortingOrderId = IntEnum("SortingOrderId", {field.name: auto() for field in SortingOrder})
