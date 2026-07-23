from pydantic.main import BaseModel


class TeamSchema(BaseModel):
    flag_url: str | None
    id: int
    name: str
    short_name: str
