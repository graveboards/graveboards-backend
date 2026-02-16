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
