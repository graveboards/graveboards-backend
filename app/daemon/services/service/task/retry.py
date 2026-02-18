from dataclasses import dataclass

from .types import TaskFailureHook, TaskMaxRetriesExceededHook
from .backoff import BackoffStrategy


@dataclass(frozen=True, slots=True)
class TaskRetryPolicy:
    backoff: BackoffStrategy | None = None
    max_retries: int | None = None
    on_failure: TaskFailureHook | None = None
    on_max_retries_exceeded: TaskMaxRetriesExceededHook | None = None
