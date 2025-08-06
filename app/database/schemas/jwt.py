from datetime import datetime
from typing import Optional

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra


class JWTSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    token: str
    issued_at: int
    expires_at: int
    is_revoked: bool = False
    updated_at: Optional[datetime] = None
