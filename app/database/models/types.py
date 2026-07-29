from __future__ import annotations
from datetime import datetime
from typing import Any

from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import DateTime, TypeDecorator


class AwareDateTime(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
        if value is None:
            return None

        if isinstance(value, str):
            value = datetime.fromisoformat(value)

        if not isinstance(value, datetime):
            raise TypeError(f"Expected datetime or ISO string, got {type(value)}")

        return value
