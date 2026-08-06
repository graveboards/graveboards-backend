"""Task specification dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .retry import TaskRetryPolicy
    from .types import TaskFactory


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """Specification for a task to be executed.

    Attributes:
        factory:
            Callable that creates the task coroutine.
        critical:
            Whether the task is critical and should not be skipped.
        retry_policy:
            Configuration for retry behavior.
    """

    factory: TaskFactory
    critical: bool = False
    retry_policy: TaskRetryPolicy | None = None
