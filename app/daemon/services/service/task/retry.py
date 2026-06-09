from dataclasses import dataclass

from .types import TaskFailureHook, TaskMaxRetriesExceededHook
from .backoff import BackoffStrategy


@dataclass(frozen=True, slots=True)
class TaskRetryPolicy:
    backoff: BackoffStrategy | None = None
    max_retries: int | None = None
    on_failure: TaskFailureHook | None = None
    on_max_retries_exceeded: TaskMaxRetriesExceededHook | None = None

    def __repr__(self) -> str:
        """Custom repr that includes backoff delay for testing."""
        backoff_info = f"({self.backoff.delay})" if self.backoff else "(None)"
        return (
            f"TaskRetryPolicy(backoff={self.backoff.__class__.__name__}{backoff_info}, "
            f"max_retries={self.max_retries}, "
            f"on_failure={self.on_failure}, "
            f"on_max_retries_exceeded={self.on_max_retries_exceeded})"
        )
