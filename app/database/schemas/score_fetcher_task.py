from datetime import datetime
from typing import Optional

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra


class ScoreFetcherTaskSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    enabled: bool = False
    last_fetch: Optional[datetime] = None


class ScoreFetcherTaskCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int
    enabled: bool = False


class ScoreFetcherTaskUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    enabled: Optional[bool] = None
    last_fetch: Optional[datetime] = None
