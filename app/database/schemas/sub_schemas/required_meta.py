"""Pydantic schema for nomination requirement counts."""

from __future__ import annotations

from pydantic.main import BaseModel


class RequiredMetaSchema(BaseModel):
    """Nomination counts required for main and non-main rulesets."""

    main_ruleset: int
    non_main_ruleset: int
