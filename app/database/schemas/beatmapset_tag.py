from typing import Optional

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra


class BeatmapsetTagSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    name: str


class BeatmapsetTagCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str


class BeatmapsetTagUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: Optional[str] = None
