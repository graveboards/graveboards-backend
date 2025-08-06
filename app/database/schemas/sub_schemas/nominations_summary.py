from typing import Optional

from pydantic.main import BaseModel

from app.osu_api.literals import RulesetLiteral

from .required_meta import RequiredMetaSchema


class NominationsSummarySchema(BaseModel):
    current: int
    eligible_main_rulesets: Optional[list[RulesetLiteral]]
    required_meta: "RequiredMetaSchema"
