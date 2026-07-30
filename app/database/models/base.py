from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm.decl_api import DeclarativeBase
from sqlalchemy.orm.base import Mapped


class Base(AsyncAttrs, DeclarativeBase):
    if TYPE_CHECKING:
        id: Mapped[int]


BaseType = TypeVar("BaseType", bound=Base)
