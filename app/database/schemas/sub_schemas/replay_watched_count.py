"""Pydantic schema for a replay watch count summary."""

from __future__ import annotations

from datetime import date

from pydantic.main import BaseModel


class ReplayWatchedCountSchema(BaseModel):
    """Count of replays watched starting from a given date."""

    start_date: date
    count: int
