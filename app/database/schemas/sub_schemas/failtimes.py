"""Pydantic schema for beatmap fail times."""

from __future__ import annotations

from pydantic.main import BaseModel


class FailtimesSchema(BaseModel):
    """Fail and exit attempt counts over a beatmap's playthrough."""

    exit: list[int] | None
    fail: list[int] | None
