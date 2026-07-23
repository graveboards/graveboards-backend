from datetime import datetime

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra


class OAuthTokenSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    access_token: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class OAuthTokenCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int
    access_token: str
    expires_at: datetime


class OAuthTokenUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    access_token: str | None = None
    expires_at: datetime | None = None
    is_revoked: bool | None = None
