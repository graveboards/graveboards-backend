"""Job load instruction dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class JobLoadInstruction:
    """Instruction for scheduling or skipping a job execution.

    Attributes:
        execution_time:
            When the job should execute.
        last_execution:
            When the job last executed.
        interval_hours:
            Interval between job executions in hours.
        skip:
            Whether the job should be skipped.
    """

    execution_time: datetime | None = None
    last_execution: datetime | None = None
    interval_hours: float | None = None
    skip: bool = False
