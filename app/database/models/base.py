"""Declarative base for all SQLAlchemy ORM models."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm.decl_api import DeclarativeBase

if TYPE_CHECKING:
    from sqlalchemy.orm.base import Mapped


class Base(AsyncAttrs, DeclarativeBase):
    """Common declarative base providing async attributes and metadata."""

    if TYPE_CHECKING:
        id: Mapped[int]


BaseType = TypeVar("BaseType", bound=Base)
