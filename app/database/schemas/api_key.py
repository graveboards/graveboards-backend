"""Pydantic schemas for API keys."""

from __future__ import annotations

from datetime import datetime

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra


class ApiKeySchema(BaseModel, BaseModelExtra):
    """API key record with its hashed value and expiry."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    hashed_key: str
    created_at: datetime | None = None
    expires_at: datetime
    is_revoked: bool = False


class ApiKeyCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to issue a new API key."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int
    hashed_key: str
    expires_at: datetime


class ApiKeyUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing API key."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    hashed_key: str | None = None
    expires_at: datetime | None = None
    is_revoked: bool | None = None
