from datetime import datetime

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Boolean
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped

from app.utils import aware_utcnow
from .base import Base


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    access_token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[int] = mapped_column(Integer, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow)
    