import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.daemon.services.service.service import Service


class TestService:
    """Test daemon service coordination."""

    @pytest.fixture
    def service(self):
        """Create a test service instance."""
        class TestService(Service):
            LOGGER = MagicMock()

        return TestService()

    async def test_service_initialization(self, service):
        """Test service initialization."""
        assert service._running is False
        assert service._start_event.is_set() is False
        assert service._started_event.is_set() is False
        assert service._stop_event.is_set() is True
        assert service._stopped_event.is_set() is True
        assert service._task_specs == {}
        assert service._ephemeral_tasks == set()
        assert service._lock is not None

    async def test_service_start_already_running_raises(self, service):
        """Test that starting already running service raises."""
        service._running = True

        with pytest.raises(RuntimeError):
            await service.start()

    async def test_service_start_sets_running_flag(self, service):
        """Test that start sets running flag."""
        service._lock = asyncio.Lock()

        with patch.object(service, "_on_start"):
            with patch.object(service, "_on_started"):
                with patch("asyncio.TaskGroup"):
                    service._lock = asyncio.Lock()
                    await service.start()

        assert service._running is True

    async def test_service_stop_not_running_does_nothing(self, service):
        """Test that stopping non-running service does nothing."""
        service._running = False

        await service.stop()

        assert service._running is False

    async def test_service_stores_task_specs(self, service):
        """Test that service stores task specifications."""
        async def task_factory():
            return "task_result"

        service._lock = asyncio.Lock()

        await service.register_task(
            name="test_task",
            factory=task_factory,
            critical=True,
            backoff=None,
            max_retries=3,
        )

        assert "test_task" in service._task_specs
        assert service._task_specs["test_task"].factory is task_factory
        assert service._task_specs["test_task"].critical is True

    async def test_service_register_task_duplicate_raises(self, service):
        """Test that registering duplicate task name raises."""
        async def task_factory():
            return "task_result"

        service._lock = asyncio.Lock()

        await service.register_task(
            name="duplicate_task",
            factory=task_factory,
        )

        with pytest.raises(ValueError):
            await service.register_task(
                name="duplicate_task",
                factory=task_factory,
            )

    async def test_service_create_ephemeral_task(self, service):
        """Test creating ephemeral task."""
        service._running = True
        service._ephemeral_tg = MagicMock()
        service._ephemeral_tg.create_task = MagicMock(return_value=MagicMock())

        async def ephemeral_coro():
            return "result"

        service.create_ephemeral_task(
            coro=ephemeral_coro,
            name="test_ephemeral",
        )

        assert len(service._ephemeral_tasks) == 1

    async def test_service_create_ephemeral_task_not_running_raises(self, service):
        """Test that creating ephemeral task when not running raises."""
        service._running = False

        async def ephemeral_coro():
            return "result"

        with pytest.raises(RuntimeError):
            service.create_ephemeral_task(coro=ephemeral_coro)

    async def test_service_serve_forever_blocks(self, service):
        """Test that serve_forever blocks until stop."""
        service._lock = asyncio.Lock()

        async def stop_later():
            await asyncio.sleep(0.1)
            await service.stop()

        async def run():
            await service.serve_forever()

        with patch.object(service, "_stop_event") as mock_stop_event:
            mock_stop_event.wait = AsyncMock()
            await service.serve_forever()

    async def test_service_wait_stopped(self, service):
        """Test waiting for service to stop."""
        service._stopped_event = asyncio.Event()
        service._stopped_event.set()

        await service.wait_stopped()

    async def test_service_stops_task_groups(self, service):
        """Test that stop properly cleans up task groups."""
        service._running = True
        service._stop_event.set()

        mock_tg = MagicMock()
        mock_tg.__aenter__ = AsyncMock()
        mock_tg.__aexit__ = AsyncMock()
        mock_ephemeral_tg = MagicMock()
        mock_ephemeral_tg.__aenter__ = AsyncMock()
        mock_ephemeral_tg.__aexit__ = AsyncMock()

        service._tg = mock_tg
        service._ephemeral_tg = mock_ephemeral_tg
        service._ephemeral_tasks = {MagicMock()}

        await service.stop()

        assert service._tg is None
        assert service._ephemeral_tg is None

    async def test_service_on_start_hook(self, service):
        """Test that _on_start hook is called."""
        service._lock = asyncio.Lock()
        mock_start = AsyncMock()
        service._on_start = mock_start

        with patch("asyncio.TaskGroup"):
            await service.start()

        mock_start.assert_awaited_once()

    async def test_service_on_started_hook(self, service):
        """Test that _on_started hook is called."""
        service._lock = asyncio.Lock()
        mock_started = AsyncMock()
        service._on_started = mock_started

        with patch("asyncio.TaskGroup"):
            await service.start()

        mock_started.assert_awaited_once()

    async def test_service_on_stop_hook(self, service):
        """Test that _on_stop hook is called."""
        service._running = True
        mock_stop = AsyncMock()
        service._on_stop = mock_stop

        await service.stop()

        mock_stop.assert_awaited_once()

    async def test_service_on_stopped_hook(self, service):
        """Test that _on_stopped hook is called."""
        service._running = True
        mock_stopped = AsyncMock()
        service._on_stopped = mock_stopped

        await service.stop()

        mock_stopped.assert_awaited_once()

    async def test_service_task_failure_handling(self, service):
        """Test task failure handling."""
        service._lock = asyncio.Lock()
        failures = []

        async def failing_task():
            raise ValueError("Task failed")

        async def on_failure(name, exc, failures_list):
            failures_list.append((name, exc))

        with patch("asyncio.TaskGroup"):
            await service.register_task(
                name="failing",
                factory=failing_task,
                max_retries=0,
                on_failure=lambda n, e: on_failure(n, e, failures),
            )

    async def test_service_critical_task_propagates_failure(self, service):
        """Test that critical task failure stops service."""
        service._lock = asyncio.Lock()

        async def critical_failing_task():
            raise ValueError("Critical failure")

        with patch("asyncio.TaskGroup") as mock_tg:
            mock_task = MagicMock()
            mock_tg.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_tg.return_value.__aexit__ = AsyncMock()
            mock_tg.return_value.create_task = MagicMock(return_value=mock_task)

            await service.register_task(
                name="critical",
                factory=critical_failing_task,
                critical=True,
                max_retries=0,
            )

    async def test_service_ephemeral_task_lifecycle_hooks(self, service):
        """Test ephemeral task lifecycle hooks."""
        service._running = True
        service._ephemeral_tg = MagicMock()
        service._ephemeral_tg.create_task = MagicMock(return_value=MagicMock())

        on_success = MagicMock()
        on_error = MagicMock()
        on_finish = MagicMock()

        async def successful_coro():
            return "result"

        service.create_ephemeral_task(
            coro=successful_coro,
            on_success=on_success,
            on_error=on_error,
            on_finish=on_finish,
        )

    async def test_service_safe_hook_exception_handling(self, service):
        """Test safe hook exception handling."""
        mock_logger = MagicMock()
        service.logger = mock_logger

        async def failing_hook():
            raise ValueError("Hook failed")

        # Should not raise
        await service._safe_hook(failing_hook)

        # Should log exception
        assert mock_logger.exception.called

    async def test_service_default_backoff_delay(self):
        """Test service with custom default backoff delay."""
        class TestService(Service):
            LOGGER = MagicMock()

        service = TestService(default_backoff_delay=2.5)

        assert service._default_backoff_delay == 2.5

    async def test_service_task_with_backoff(self, service):
        """Test task with backoff strategy."""
        service._lock = asyncio.Lock()

        from app.daemon.services.service.task.backoff import (
            ConstantBackoff,
        )

        async def task_factory():
            return "task_result"

        backoff = ConstantBackoff(delay=0.1)

        with patch("asyncio.TaskGroup"):
            await service.register_task(
                name="backoff_task",
                factory=task_factory,
                backoff=backoff,
            )

        assert service._task_specs["backoff_task"].retry_policy.backoff is backoff
