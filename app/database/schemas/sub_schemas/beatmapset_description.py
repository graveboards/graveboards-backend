from pydantic.main import BaseModel


class BeatmapsetDescriptionSchema(BaseModel):
    description: str
