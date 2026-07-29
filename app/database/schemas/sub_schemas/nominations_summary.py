from __future__ import annotations
from pydantic.main import BaseModel

from app.osu_api.literals import RulesetLiteral

from .required_meta import RequiredMetaSchema


class NominationsSummarySchema(BaseModel):
    current: int
    eligible_main_rulesets: list[RulesetLiteral] | None
    required_meta: RequiredMetaSchema
