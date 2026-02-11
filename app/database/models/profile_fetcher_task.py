from datetime import datetime
from typing import Optional

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer, DateTime, Boolean
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped

from .base import Base


class ProfileFetcherTask(Base):
    __tablename__ = "profile_fetcher_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fetch: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
