from datetime import datetime
from typing import Optional

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra


class OAuthTokenSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    access_token: str
    expires_at: int
    is_revoked: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
