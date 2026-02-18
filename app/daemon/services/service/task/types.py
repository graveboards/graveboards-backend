from collections.abc import Awaitable, Callable
from typing import Any

type TaskFactory = Callable[[], Awaitable[Any]]
type TaskFailureHook = Callable[[str, Exception, int], Awaitable[None]]
type TaskMaxRetriesExceededHook = Callable[[str, int], Awaitable[None]]
type TaskSuccessHook = Callable[[Any], Awaitable[None] | None]
type TaskErrorHook = Callable[[Exception], Awaitable[None] | None]
type TaskFinishHook = Callable[[], Awaitable[None] | None]
