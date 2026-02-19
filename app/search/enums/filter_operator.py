from enum import Enum
from typing import Callable

from sqlalchemy.sql import operators


class FilterOperator(Enum):
    """Supported filter operators for query conditions.

    Each operator maps:
        - A public string identifier (e.g., ``"eq"``)
        - A callable that applies the operation to a database column

    This decouples external query syntax from ORM-specific logic.
    """
    EQ = "eq", staticmethod(operators.eq)
    NEQ = "neq", staticmethod(operators.ne)
    GT = "gt", staticmethod(operators.gt)
    LT = "lt", staticmethod(operators.lt)
    GTE = "gte", staticmethod(operators.ge)
    LTE = "lte", staticmethod(operators.le)
    IN = "in", staticmethod(lambda col, val: col.in_(val))
    NOT_IN = "not_in", staticmethod(lambda col, val: ~col.in_(val))
    IS_NULL = "is_null", staticmethod(lambda col, val: col.is_(None) if val else col.is_not(None))
    REGEX = "regex", staticmethod(lambda col, val: col.op("~")(val))
    NOT_REGEX = "not_regex", staticmethod(lambda col, val: col.op("!~")(val))

    def __init__(self, value: str, method: Callable):
        self._value_ = value
        self.method = method

    @classmethod
    def from_name(cls, name: str) -> "FilterOperator":
        """Resolve an operator from its string name.

        Args:
            name:
                Case-insensitive operator name.

        Returns:
            Matching ``FilterOperator``.

        Raises:
            ValueError:
                If no matching operator exists.
        """
        for member_name, member in cls.__members__.items():
            if name.upper() == member_name:
                return member

        raise ValueError(f"No FilterOperator exists by the name of '{name}'")
