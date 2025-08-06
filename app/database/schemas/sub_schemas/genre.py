from pydantic.main import BaseModel
from app.osu_api.literals import GenreIdLiteral, GenreNameLiteral


class GenreSchema(BaseModel):
    id: GenreIdLiteral
    name: GenreNameLiteral
