"""Pydantic schema for a group a user belongs to."""

from __future__ import annotations

from app.osu_api.literals import RulesetLiteral

from .group import GroupSchema


class UserGroupSchema(GroupSchema):
    """Group metadata plus the rulesets the user plays in that group."""

    playmodes: list[RulesetLiteral] | None
