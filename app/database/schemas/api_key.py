from datetime import datetime
from typing import Optional

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra


class ApiKeySchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    key: str
    created_at: Optional[datetime] = None
    expires_at: datetime
    is_revoked: bool = False
