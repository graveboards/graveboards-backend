from dataclasses import dataclass

from .retry import TaskRetryPolicy
from .types import TaskFactory


@dataclass(frozen=True, slots=True)
class TaskSpec:
    factory: TaskFactory
    critical: bool = False
    retry_policy: TaskRetryPolicy | None = None
