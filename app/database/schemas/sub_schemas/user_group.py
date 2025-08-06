from typing import Optional

from app.osu_api.literals import RulesetLiteral
from .group import GroupSchema


class UserGroupSchema(GroupSchema):
    playmodes: Optional[list[RulesetLiteral]]
