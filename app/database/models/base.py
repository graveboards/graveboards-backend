from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm.decl_api import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    pass


BaseType = TypeVar("BaseType", bound=Base)
