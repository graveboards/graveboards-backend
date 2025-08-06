from pydantic.main import BaseModel


class HypeSchema(BaseModel):
    current: int
    required: int
