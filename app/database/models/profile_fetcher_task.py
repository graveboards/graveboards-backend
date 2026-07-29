from __future__ import annotations
from datetime import datetime

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer

from .base import Base


class ProfileFetcherTask(Base):
    __tablename__ = "profile_fetcher_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fetch: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
