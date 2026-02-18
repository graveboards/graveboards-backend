import asyncio
from typing import ClassVar, Never

from app.logging import Logger
from .services import Service, ServiceFactory
from .services.service.task import BackoffStrategy, TaskFailureHook, TaskMaxRetriesExceededHook


class ServiceSupervisor(Service):
    """Supervises and manages the lifecycle of child ``Service`` instances.

    Child services are instantiated and executed as managed tasks within the
    supervisor's structured concurrency scope.

    Subclasses must define the ``LOGGER`` class variable.
    """

    LOGGER: ClassVar[Logger | None] = None

    def __init__(self):
        """Initialize the supervisor."""
        super().__init__()
        self._services: dict[str, Service] = {}
        self._service_lock = asyncio.Lock()

    async def register_service(
        self,
        name: str,
        factory: ServiceFactory,
        backoff: BackoffStrategy = None,
        max_retries: int = None,
        on_failure: TaskFailureHook | None = None,
        on_max_retries_exceeded: TaskMaxRetriesExceededHook | None = None,
    ) -> None:
        """Register a service type for supervised execution.

        A new instance of ``service_type`` is created for each run attempt.
        Retry and failure behavior is delegated to the base ``Service`` task
        management system.

        Args:
            name:
                Unique identifier for the service.
            factory:
                Callable that returns an instance of ``Service`` or a subclass.
            backoff:
                Optional backoff strategy for retries.
            max_retries:
                Maximum retry attempts (``None`` for unlimited).
            on_failure:
                Optional failure hook.
            on_max_retries_exceeded:
                Optional terminal failure hook.

        Raises:
            ValueError:
                If a service with the same name is already registered.
            TypeError:
                If ``factory`` doesn't return a ``Service`` subclass.
        """
        async with self._service_lock:
            if name in self._services:
                raise ValueError(f"Service '{name}' already registered")

            service = factory()

            if not isinstance(service, Service):
                raise TypeError("Factory must return a Service instance")

            self._services[name] = service

            async def runner() -> None:
                try:
                    await service.start()
                    await service.serve_forever()
                finally:
                    async with self._service_lock:
                        self._services.pop(name, None)

            await super().register_task(
                name,
                runner,
                backoff=backoff,
                max_retries=max_retries,
                on_failure=on_failure,
                on_max_retries_exceeded=on_max_retries_exceeded
            )

    async def wait_stopped(self) -> None:
        async with self._service_lock:
            services = tuple(service for service in self._services.values())

        await asyncio.gather(*(service.wait_stopped() for service in services))

    async def stop_service(self, name: str) -> None:
        """Stop and wait on a running service.

        Args:
            name:
                Unique identifier for the service.

        Raises:
            ValueError:
                If the service is not registered.
        """
        if name not in self._services:
            raise ValueError(f"Service '{name}' is not registered")

        async with self._service_lock:
            service = self._services[name]

        await service.stop()
        await service.wait_stopped()

        async with self._service_lock:
            self._services.pop(name, None)

    async def register_task(self, *args, **kwargs) -> Never:
        """Not supported by ``ServiceSupervisor``.

        Raises:
            RuntimeError
        """
        raise RuntimeError(
            "ServiceSupervisor does not support register_task(). "
            f"Use {self.register_service.__name__}() instead."
        )

    async def create_ephemeral_task(self, *args, **kwargs) -> Never:
        """Not supported by ``ServiceSupervisor``.

        Raises:
            RuntimeError"""
        raise RuntimeError("ServiceSupervisor does not support ephemeral tasks.")

    async def _on_stop(self) -> None:
        """Stop all services before shutdown"""
        async with self._service_lock:
            services = dict(self._services)

        for name, service in services.items():
            await self.stop_service(name)
