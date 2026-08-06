"""Pydantic schemas for OAuth tokens."""

from __future__ import annotations

from datetime import datetime

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra


class OAuthTokenSchema(BaseModel, BaseModelExtra):
    """OAuth access token record with its expiry and revocation state."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    access_token: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class OAuthTokenCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to issue a new OAuth token."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int
    access_token: str
    expires_at: datetime


class OAuthTokenUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing OAuth token."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    access_token: str | None = None
    expires_at: datetime | None = None
    is_revoked: bool | None = None
