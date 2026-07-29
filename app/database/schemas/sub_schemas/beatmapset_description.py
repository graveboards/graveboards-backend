from __future__ import annotations
from pydantic.main import BaseModel


class BeatmapsetDescriptionSchema(BaseModel):
    description: str
