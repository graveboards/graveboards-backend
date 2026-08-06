"""Custom SQLAlchemy type decorators for database models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.types import DateTime, TypeDecorator

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect


class AwareDateTime(TypeDecorator):
    """Stores timezone-aware datetimes, coercing naive/ISO input."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: Any, _dialect: Dialect) -> Any:
        """Coerce ``value`` to a timezone-aware ``datetime`` before binding."""
        if value is None:
            return None

        if isinstance(value, str):
            value = datetime.fromisoformat(value)

        if not isinstance(value, datetime):
            raise TypeError(f"Expected datetime or ISO string, got {type(value)}")

        return value
