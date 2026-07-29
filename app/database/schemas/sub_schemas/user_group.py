from __future__ import annotations
from app.osu_api.literals import RulesetLiteral

from .group import GroupSchema


class UserGroupSchema(GroupSchema):
    playmodes: list[RulesetLiteral] | None
