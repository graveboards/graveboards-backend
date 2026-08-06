"""Application-wide enumerations."""

from __future__ import annotations

from enum import Enum

__all__ = ["Env"]


class Env(Enum):
    """Application environment."""

    PROD = "prod"
    DEV = "dev"
    TEST = "test"
