from datetime import datetime
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JobLoadInstruction:
    execution_time: datetime | None = None
    last_execution: datetime | None = None
    interval_hours: float | None = None
    skip: bool = False
