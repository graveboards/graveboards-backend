from datetime import datetime

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra


class ApiKeySchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    hashed_key: str
    created_at: datetime | None = None
    expires_at: datetime
    is_revoked: bool = False


class ApiKeyCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int
    hashed_key: str
    expires_at: datetime


class ApiKeyUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    hashed_key: str | None = None
    expires_at: datetime | None = None
    is_revoked: bool | None = None
