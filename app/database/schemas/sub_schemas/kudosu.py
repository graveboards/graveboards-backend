from pydantic.main import BaseModel


class KudosuSchema(BaseModel):
    available: int
    total: int
