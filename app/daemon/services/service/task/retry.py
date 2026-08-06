"""Retry policy configuration for task execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .backoff import BackoffStrategy
    from .types import TaskFailureHook, TaskMaxRetriesExceededHook


@dataclass(frozen=True, slots=True)
class TaskRetryPolicy:
    """Configuration for task retry behavior.

    Attributes:
        backoff:
            Strategy for determining retry delays.
        max_retries:
            Maximum number of retry attempts.
        on_failure:
            Hook called on each retry failure.
        on_max_retries_exceeded:
            Hook called when max retries are exceeded.
    """

    backoff: BackoffStrategy | None = None
    max_retries: int | None = None
    on_failure: TaskFailureHook | None = None
    on_max_retries_exceeded: TaskMaxRetriesExceededHook | None = None

    def __repr__(self) -> str:
        """Custom repr that includes backoff delay for testing."""
        backoff_info = f"({self.backoff.next_delay()})" if self.backoff else "(None)"
        return (
            f"TaskRetryPolicy(backoff={self.backoff.__class__.__name__}{backoff_info}, "
            f"max_retries={self.max_retries}, "
            f"on_failure={self.on_failure}, "
            f"on_max_retries_exceeded={self.on_max_retries_exceeded})"
        )
