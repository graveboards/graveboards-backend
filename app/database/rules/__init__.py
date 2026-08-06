"""Public API for the rules engine: base classes, execution context and the rule registry."""

from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase, DatabaseRestrictionBase, RestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.rules.registry import (
    RULE_REGISTRY,
    RULE_TIERS,
    get_supported_versions,
    get_validator,
    get_validator_tier,
    get_validators_for_tier,
    register_validator,
)

__all__ = [
    "RULE_REGISTRY",
    "RULE_TIERS",
    "BeatmapRestrictionBase",
    "DatabaseRestrictionBase",
    "ExecutionContext",
    "RestrictionBase",
    "RuleViolationError",
    "get_supported_versions",
    "get_validator",
    "get_validator_tier",
    "get_validators_for_tier",
    "register_validator",
]
