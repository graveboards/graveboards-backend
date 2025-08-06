from typing import TypeVar

from sqlalchemy.orm.decl_api import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


BaseType = TypeVar("BaseType", bound=Base)
