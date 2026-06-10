from datetime import datetime
from typing import Optional

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra


class ApiKeySchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    hashed_key: str
    created_at: Optional[datetime] = None
    expires_at: datetime
    is_revoked: bool = False


class ApiKeyCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int
    hashed_key: str
    expires_at: datetime


class ApiKeyUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    hashed_key: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_revoked: Optional[bool] = None
