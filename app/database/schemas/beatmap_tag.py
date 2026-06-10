from typing import Optional
from datetime import datetime

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra


class BeatmapTagSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ruleset_id: Optional[int]
    description: str
    created_at: datetime
    updated_at: datetime


class BeatmapTagCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str
    ruleset_id: Optional[int] = None
    description: str


class BeatmapTagUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: Optional[str] = None
    ruleset_id: Optional[int] = None
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
