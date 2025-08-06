from pydantic.main import BaseModel

from app.osu_api.literals import RulesetLiteral


class RankHistorySchema(BaseModel):
    mode: RulesetLiteral
    data: list[int]
