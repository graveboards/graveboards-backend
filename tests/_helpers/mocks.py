"""Shared test doubles used across the integration/unit suites.

Keep this module named WITHOUT a `test_` prefix so pytest never collects it.
Import from tests as:  from tests._helpers.mocks import MockSession, MockLockCtx
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock


class MockLockCtx:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *args: Any) -> None:
        pass


class MockSession:
    def __init__(self, session: Any = None) -> None:
        self._session = session or AsyncMock()

    def __call__(self) -> MockSession:
        return MockSession(session=self._session)

    async def __aenter__(self) -> Any:
        return self._session

    async def __aexit__(self, *args: Any) -> None:
        pass


def mock_redis_client(*, lock_ctx: Any = None) -> AsyncMock:
    rc = AsyncMock()
    rc.hgetall = AsyncMock(return_value=None)
    rc.hset = AsyncMock(return_value=None)
    rc.expire = AsyncMock(return_value=None)
    rc.incr = AsyncMock(return_value=1)
    rc.lock_ctx = MagicMock(return_value=lock_ctx or MockLockCtx())
    return rc
