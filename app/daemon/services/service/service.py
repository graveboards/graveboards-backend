import asyncio
from typing import Awaitable, Any, ClassVar, Callable

from app.logging import Logger
from .task import (
    TaskFactory,
    TaskSpec,
    BackoffStrategy,
    TaskRetryPolicy,
    TaskFailureHook,
    TaskMaxRetriesExceededHook,
    TaskSuccessHook,
    TaskErrorHook,
    TaskFinishHook
)


class Service:
    """Base class for asynchronous services.

    This class provides:
        - Dynamic registration of named tasks at runtime
        - Automatic task restart with backoff and retry policies
        - Lifecycle and failure hooks
        - Critical task escalation

    Subclasses must define the ``LOGGER`` class variable.
    """

    LOGGER: ClassVar[Logger | None] = None

    def __init__(
        self,
        default_backoff_delay: float = 0.0
    ) -> None:
        """Initialize the service.

        Args:
            default_backoff_delay:
                Fallback backoff delay for tasks without one configured
        """
        if self.LOGGER is None:
            raise TypeError("Subclasses must define the LOGGER class variable")

        self.logger = self.LOGGER
        self._default_backoff_delay = default_backoff_delay
        self._running = False
        self._start_event = asyncio.Event()
        self._started_event = asyncio.Event()
        self._stop_event = asyncio.Event()
        self._stopped_event = asyncio.Event()
        self._stopped_event.set()
        self._tg: asyncio.TaskGroup | None = None
        self._task_specs: dict[str, TaskSpec] = {}
        self._ephemeral_tg: asyncio.TaskGroup | None = None
        self._ephemeral_tasks: set[asyncio.Task] = set()
        self._lock = asyncio.Lock()

    async def register_task(
        self,
        name: str,
        factory: TaskFactory,
        *,
        critical: bool = False,
        backoff: BackoffStrategy = None,
        max_retries: int = None,
        on_failure: TaskFailureHook | None = None,
        on_max_retries_exceeded: TaskMaxRetriesExceededHook | None = None
    ) -> None:
        """Register a task to run under the service's lifecycle.

        If the service is already running, the task will be started immediately.

        This should be used for long-running managed tasks. For short-lived tasks, use
        ``create_ephemeral_task``.

        Args:
            name:
                Unique identifier for the task.
            factory:
                Asynchronous callable that implements the task.
            critical:
                Whether failure of this task should propagate and stop the service.
            backoff:
                Optional backoff strategy for retries.
            max_retries:
                Maximum retry attempts (``None`` for unlimited).
            on_failure:
                Optional failure hook.
            on_max_retries_exceeded:
                Optional terminal failure hook.

        Raises:
            ValueError: If a task with the same name is already registered.
        """
        async with self._lock:
            if name in self._task_specs:
                raise ValueError(f"Task '{name}' already registered")

            retry_policy = TaskRetryPolicy(backoff, max_retries, on_failure, on_max_retries_exceeded)
            spec = TaskSpec(factory, critical, retry_policy)
            self._task_specs[name] = spec

            if self._running and self._tg:
                self._start_task(name, spec)

    async def start(self) -> None:
        """
        Start the service and all registered tasks.

        Executes ``_on_start`` and ``_on_started`` lifecycle hooks.

        Raises:
            RuntimeError: If already running.
        """
        async with self._lock:
            if self._running:
                raise RuntimeError("Service already running")

            self._running = True
            self._stop_event.clear()
            self._stopped_event.clear()
            self._start_event.set()

        await self._on_start()

        async with self._lock:
            self._tg = asyncio.TaskGroup()
            self._ephemeral_tg = asyncio.TaskGroup()
            await self._tg.__aenter__()
            await self._ephemeral_tg.__aenter__()

            for name, spec in self._task_specs.items():
                self._start_task(name, spec)

            self._started_event.set()

        await self._on_started()

    async def stop(self) -> None:
        """Stop the service and wait for all tasks to exit.

        This sets the internal stop event, allowing ``serve_forever`` to exit and tasks to be
        canceled gracefully.

        Executes ``_on_stop`` and ``_on_stopped`` lifecycle hooks.
        """
        async with self._lock:
            if not self._running:
                return

            self._stop_event.set()

        try:
            await self._on_stop()
        finally:
            async with self._lock:
                if self._ephemeral_tg:
                    for task in self._ephemeral_tasks:
                        task.cancel()

                    await self._ephemeral_tg.__aexit__(None, None, None)
                    self._ephemeral_tg = None

                if self._tg:
                    await self._tg.__aexit__(None, None, None)
                    self._tg = None

                self._running = False
                self._stopped_event.set()

            await self._on_stopped()

    async def serve_forever(self) -> None:
        """Block until ``stop`` is called."""
        await self._main()

    async def wait_stopped(self) -> None:
        """Wait until the service has fully stopped."""
        await self._stopped_event.wait()

    def create_ephemeral_task(
        self,
        coro: Awaitable[Any],
        *,
        name: str | None = None,
        on_success: TaskSuccessHook | None = None,
        on_error: TaskErrorHook | None = None,
        on_finish: TaskFinishHook | None = None,
    ) -> None:
        """
        Schedule a short-lived coroutine to run under the service.

        Unlike ``register_task``, this method is designed for fire-and-forget or finite
        jobs that should not impact the service lifecycle.

        Optional lifecycle hooks may be executed on success, failure, or completion.

        Hooks may return an awaitable; if so, it will be awaited. Any exceptions raised
        by hooks are suppressed to prevent destabilizing the service.

        Args:
            coro:
                The coroutine to execute.
            name:
                Optional task identifier for debugging and introspection.
            on_success:
                Optional hook called with the coroutine's result if it completes
                successfully.
            on_error:
                Optional hook called with the raised exception if the coroutine fails.
            on_finish:
                Optional hook called after the coroutine finishes regardless of outcome.

        Raises:
            RuntimeError:
                If the service is not currently running.
        """
        if not self._running:
            raise RuntimeError("Service not running")

        async def wrapper() -> None:
            try:
                result = await coro
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if on_error:
                    await self._safe_hook(on_error, exc)
            else:
                if on_success:
                    await self._safe_hook(on_success, result)
            finally:
                if on_finish:
                    await self._safe_hook(on_finish)

        task = self._ephemeral_tg.create_task(wrapper(), name=name)
        self._ephemeral_tasks.add(task)
        task.add_done_callback(self._ephemeral_tasks.discard)

    async def _main(self) -> None:
        """Default main loop of the service.

        By default, waits until ``stop`` is called.

        Subclasses can override to implement custom main loop behavior.
        """
        await self._stop_event.wait()

    async def _on_start(self) -> None:
        """Execute before the ``TaskGroup`` is started.

        Subclasses can override to perform setup before tasks start.
        """
        pass

    async def _on_started(self) -> None:
        """Execute immediately after tasks have been started.

        Subclasses can override to perform actions that require tasks to be running.
        """
        pass

    async def _on_stop(self) -> None:
        """Execute after stop is requested but before the ``TaskGroup`` exits.

        Subclasses can override to perform cleanup or pre-cancellation actions.
        """
        pass

    async def _on_stopped(self) -> None:
        """Execute after all tasks are canceled and the service is stopped.

        Subclasses can override to perform final cleanup.
        """
        pass

    async def _on_task_failure(
        self,
        name: str,
        exc: Exception,
        failures: int,
        spec: TaskSpec
    ) -> None:
        """Execute whenever a task fails, before retrying.

        Runs after the task's per-task ``on_failure`` hook, if configured.

        Subclasses can override to perform logging, alerting, or metrics.

        Args:
            name:
                Unique identifier for the task.
            exc:
                Exception raised by the task.
            failures:
                Number of failures that have occurred for this task.
            spec:
                Object containing task factory, critical flag, and ``RetryPolicy``.
        """
        pass

    async def _on_critical_failure(
        self,
        name: str,
        exc: Exception,
        spec: TaskSpec
    ) -> None:
        """Execute when a critical task fails.

        Runs after the task's normal failure hooks and before the exception propagates
        to stop the service.

        Subclasses can override to perform logging, alerting, or metrics.

        Args:
            name:
                Unique identifier for the task.
            exc:
                The exception raised by the critical task.
            spec:
                Object containing task factory, critical flag, and ``RetryPolicy``.
        """
        pass

    def _start_task(
        self,
        name: str,
        spec: TaskSpec
    ) -> None:
        """Start a single task under structured concurrency with retry logic.

        This wraps the task factory in a runner coroutine that:
            - Handles retries with optional backoff
            - Calls per-task and global failure hooks
            - Respects critical task escalation

        Args:
            name:
                Unique identifier for the task.
            spec:
                Object containing task factory, critical flag, and ``RetryPolicy``.

        Raises:
            RuntimeError:
                If the service is not currently running.
        """
        if not self._running:
            raise RuntimeError("Service not running")

        async def runner() -> None:
            retry_policy = spec.retry_policy
            failures = 0

            while True:
                try:
                    await spec.factory()

                    if retry_policy.backoff:
                        retry_policy.backoff.reset()

                    return
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    failures += 1

                    if retry_policy.on_failure:
                        await self._safe_hook(retry_policy.on_failure, name, exc, failures)

                    await self._safe_hook(self._on_task_failure, name, exc, failures, spec)

                    if spec.critical:
                        await self._safe_hook(self._on_critical_failure, name, exc, spec)
                        raise

                    is_exhausted = (
                        retry_policy.max_retries is not None
                        and failures > retry_policy.max_retries
                    )

                    if is_exhausted:
                        if retry_policy.on_max_retries_exceeded:
                            await self._safe_hook(retry_policy.on_max_retries_exceeded, name, failures)

                        if retry_policy.backoff:
                            retry_policy.backoff.reset()

                        return

                    delay = (
                        retry_policy.backoff.next_delay()
                        if retry_policy.backoff
                        else self._default_backoff_delay
                    )

                    await asyncio.sleep(delay)

        self._tg.create_task(runner(), name=name)

    async def _safe_hook(
        self,
        hook: Callable[..., Awaitable[Any] | None],
        *args: Any,
        **kwargs: Any
    ) -> None:
        """Run a hook safely, awaiting if it returns a coroutine."""
        try:
            if maybe := hook(*args, **kwargs):
                await maybe
        except Exception:
            self.logger.exception(
                f"{self.__class__.__name__}.{hook.__name__} "
                f"raised for args={args}, kwargs={kwargs}"
            )
