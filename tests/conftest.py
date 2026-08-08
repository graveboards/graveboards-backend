"""
Test configuration and shared fixtures for the Graveboards backend test suite.

--- How to run tests ---

  make test         # Dockerized: PostgreSQL + Redis in containers, pytest -v
  pytest            # Local: requires PostgreSQL + Redis at localhost per .env.test

The Makefile Docker target is the authoritative CI path.  Local pytest is
convenient during development but needs companion services running.

--- Fixture hierarchy ---

  _engine_pool (session)  → engine + tables created once per session
  db_session (function)   → per-test connection rolled back after test
  db_transaction (function) → same but with a savepoint (commits visible within test)

  test_client (function)  → full Connexion app with mock middleware
  test_client_with_mocks (function) → factory for custom-mock TestClient
  admin_user_token (function) → JWT for admin user ID 11111111
  security_disabled / security_enabled → context managers
  authenticated_user_id → patches get_authenticated_user_id

--- Timing ---

  Set GRAVEBOARDS_TEST_TIMING=1 for per-test and per-fixture timing output.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from contextlib import ExitStack, suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

# ---------------------------------------------------------------------------
# Engine / table cache (session-scoped so DB is provisioned once)
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_tables_ready: bool = False

# ---------------------------------------------------------------------------
# Timing instrumentation (enable with GRAVEBOARDS_TEST_TIMING=1)
# ---------------------------------------------------------------------------

ENABLE_TIMING: bool = os.getenv("GRAVEBOARDS_TEST_TIMING") in ("1", "true", "yes")

_timing_data: dict[str, float] = {}
_fixture_timing: dict[str, float] = {}


def _clear_spec_cache() -> None:
    if os.getenv("GRAVEBOARDS_CLEAR_SPEC_CACHE") not in ("1", "true", "yes"):
        return
    project_root = Path(__file__).resolve().parents[1]
    for p in (
        project_root / "instance" / ".spec_cache.pkl",
        project_root / "api" / "v1" / "spec" / ".spec_cache.pkl",
    ):
        if p.exists():
            p.unlink()


def pytest_configure(config: Any) -> None:
    # --- Load .env.test *first*, before any app module reads env vars ---
    # Config.__init__() is lazily imported inside _ensure_engine(), so this
    # runs earlier and populates os.environ with DB/redis/security settings.
    _env_test = Path(__file__).resolve().parents[1] / ".env.test"
    if _env_test.exists():
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=_env_test, override=True)

    os.environ["DISABLE_SECURITY"] = "false"
    os.environ.setdefault("ENV", "test")

    # Validate: without these, every integration test will fail with
    # opaque connection errors.  Fail fast with a clear message.
    _required = (
        "POSTGRESQL_HOST",
        "POSTGRESQL_PORT",
        "POSTGRESQL_USERNAME",
        "POSTGRESQL_PASSWORD",
        "POSTGRESQL_DATABASE",
        "REDIS_HOST",
        "REDIS_PORT",
    )
    _missing = [k for k in _required if not os.getenv(k)]

    # Only enforce the DB/Redis env requirement when integration or e2e tests are
    # actually in scope. Pure `pytest -m unit` must be runnable with no infrastructure.
    _markexpr = config.getoption("-m") or ""
    _only_unit = _markexpr.strip() == "unit"
    _collecting_all = not _markexpr.strip()
    _needs_infra = _collecting_all or not _only_unit

    if _missing and _needs_infra:
        pytest.exit(
            f"Missing env vars: {', '.join(_missing)}. "
            f"Source .env.test before running integration/e2e tests:\n"
            f"  make test-all   (recommended)\n"
            f"  or: set -a && source .env.test && set +a && pytest ...",
            returncode=1,
        )

    _clear_spec_cache()


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-assign layer + cross-cutting markers based on each test's directory.

    A test gets exactly one *layer* marker (unit / integration / e2e) from its
    directory. Explicit `@pytest.mark.X` decorators always win. `security` and
    `search` are cross-cutting tags that stack on top of the layer marker.

    IMPORTANT: we must use `item.get_closest_marker(name)` to decide whether a
    marker already exists — NOT `name in item.keywords`. `item.keywords` in
    pytest also contains path/name-chain segments, so for a test under
    `tests/unit/` the string "unit" is already in `item.keywords` (from the
    directory name), which silently disabled the previous auto-marker.
    """
    root = Path(str(config.rootpath))
    for item in items:
        try:
            rel = Path(str(item.fspath)).relative_to(root).as_posix()
        except ValueError:
            rel = str(item.fspath)

        if rel.startswith("tests/unit/"):
            if item.get_closest_marker("unit") is None:
                item.add_marker(pytest.mark.unit)
        elif rel.startswith("tests/integration/"):
            if item.get_closest_marker("integration") is None:
                item.add_marker(pytest.mark.integration)
        elif rel.startswith("tests/e2e/"):
            if item.get_closest_marker("e2e") is None:
                item.add_marker(pytest.mark.e2e)

        if "tests/security/" in rel and item.get_closest_marker("security") is None:
            item.add_marker(pytest.mark.security)
        if "tests/search/" in rel and item.get_closest_marker("search") is None:
            item.add_marker(pytest.mark.search)

        if (
            item.get_closest_marker("db_session") is not None
            or item.get_closest_marker("db_transaction") is not None
        ):
            if (
                item.get_closest_marker("integration") is None
                and item.get_closest_marker("unit") is None
            ):
                item.add_marker(pytest.mark.integration)


@pytest.hookimpl(trylast=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> None:
    """Collect timing for each test phase (setup / call / teardown)."""
    if not ENABLE_TIMING:
        return
    phase = call.when
    duration = call.stop - call.start
    key = f"{item.nodeid}::{phase}"
    _timing_data[key] = duration


@pytest.hookimpl(trylast=True)
def pytest_fixture_setup(
    fixturedef: pytest.FixtureDef[Any], request: pytest.FixtureRequest
) -> object | None:
    """Time the *setup* portion of every fixture."""
    if not ENABLE_TIMING:
        return None
    start = time.perf_counter()
    request.node.stash[f"_fixture_start_{fixturedef.argname}"] = start
    return None


@pytest.hookimpl(tryfirst=True)
def pytest_fixture_post_finalizer(
    fixturedef: pytest.FixtureDef[Any], request: pytest.FixtureRequest
) -> None:
    """Time the full lifecycle (setup+teardown) of every fixture."""
    if not ENABLE_TIMING:
        return
    key = f"_fixture_start_{fixturedef.argname}"
    start = request.node.stash.get(key)
    if start is not None:
        elapsed = time.perf_counter() - start
        _fixture_timing[f"{request.node.nodeid}::{fixturedef.argname}"] = elapsed
        # Stash has no pop(); leaving the entry is harmless (the node is discarded
        # after the test), but clearing keeps the stash small on long sessions.
        with suppress(KeyError):
            del request.node.stash[key]


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, exitstatus: int, config: pytest.Config
) -> None:
    """Print timing summaries when GRAVEBOARDS_TEST_TIMING is enabled."""
    if not ENABLE_TIMING:
        return

    terminalreporter.section("⏱ Timing: slowest tests", sep="=", bold=True)
    test_durations: dict[str, float] = {}
    for key, duration in _timing_data.items():
        if key.endswith("::call"):
            test_durations[key.removesuffix("::call")] = duration
    for nodeid, duration in sorted(test_durations.items(), key=lambda x: -x[1])[:30]:
        terminalreporter.write_line(f"  {duration:7.3f}s  {nodeid}")

    terminalreporter.section("⏱ Timing: slowest fixtures", sep="=", bold=True)
    for key, duration in sorted(_fixture_timing.items(), key=lambda x: -x[1])[:20]:
        terminalreporter.write_line(f"  {duration:7.3f}s  {key}")

    # Fixture aggregate costs
    agg: dict[str, float] = {}
    for key, duration in _fixture_timing.items():
        name = key.rsplit("::", 1)[-1]
        agg[name] = agg.get(name, 0) + duration
    terminalreporter.section("⏱ Fixture cumulative cost", sep="=", bold=True)
    for name, total in sorted(agg.items(), key=lambda x: -x[1]):
        terminalreporter.write_line(f"  {total:7.3f}s  {name}")


# ---------------------------------------------------------------------------
# DB engine (session-scoped — created once, dropped at exit)
# ---------------------------------------------------------------------------


async def _ensure_engine() -> AsyncEngine:
    """Lazily create the engine, create_all tables, return the engine."""
    global _engine, _tables_ready

    if _engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine

        from app.database.db import DATABASE_URI

        _engine = create_async_engine(
            DATABASE_URI,
            pool_size=10,
            max_overflow=0,
            pool_pre_ping=False,
        )

    if not _tables_ready:
        from sqlalchemy.exc import IntegrityError, OperationalError

        from app.database.models import Base

        try:
            async with _engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except (IntegrityError, OperationalError):
            pass
        _tables_ready = True

    return _engine


async def _teardown_engine() -> None:
    """Drop all tables and dispose the engine (called on suite exit).

    Suppresses connection errors so a unit-only run (no DB available) does
    not hang at session exit when a ``db_session``-using test already
    created the engine object but failed to connect.
    """
    global _engine, _tables_ready
    if _engine is not None:
        try:
            from app.database.models import Base

            async with _engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            pass
        with suppress(Exception):
            await _engine.dispose()
        _engine = None
        _tables_ready = False


def _run_async_teardown() -> None:
    """Synchronous wrapper for engine teardown at session exit."""
    import asyncio as _asyncio

    try:
        loop = _asyncio.get_running_loop()
    except RuntimeError:
        loop = _asyncio.new_event_loop()
    if loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(_asyncio.run, _teardown_engine()).result()
    else:
        loop.run_until_complete(_teardown_engine())


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up the cached engine after the entire test session."""
    _run_async_teardown()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session() -> Any:
    """Provide a per-test database session whose changes are never persisted.

    Creates the engine and tables ONCE across the entire test session.
    Each test gets its own connection + transaction; everything is rolled
    back after the test so tests never leak state to each other.
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    engine = await _ensure_engine()
    conn = await engine.connect()
    trans = await conn.begin()

    session = AsyncSession(
        bind=conn,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await conn.close()


@pytest.fixture
async def db_transaction() -> Any:
    """Same as db_session but savepoints allow intra-test commits to be visible.

    Use when a test seeds data then queries it via a new session (e.g. the
    search engine, which opens its own connection).  The outer rollback at
    teardown still isolates the test from all others.
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    engine = await _ensure_engine()
    conn = await engine.connect()
    trans = await conn.begin()

    session = AsyncSession(
        bind=conn,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await conn.close()


# ---------------------------------------------------------------------------
# TestClient fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def security_disabled() -> Any:
    from app.config import override_security_enabled

    with override_security_enabled(False):
        yield


@pytest.fixture
def security_enabled() -> Any:
    from app.config import override_security_enabled

    with override_security_enabled(True):
        yield


@pytest.fixture
def authenticated_user_id() -> Callable[[int], Any]:
    """Return a context-manager factory that patches ``get_authenticated_user_id``
    in every decorator module that imports it.
    """

    def _patch(user_id: int) -> Any:
        stack = ExitStack()
        for module in (
            "app.security.decorators.role_authorization",
            "app.security.decorators.auth_context",
            "app.security.decorators.ownership_authorization",
            "app.security.decorators.ownership_filter",
            "app.security.decorators.utils",
        ):
            stack.enter_context(patch(f"{module}.get_authenticated_user_id", return_value=user_id))
        return stack

    return _patch


def _patch_all_auth_modules(user_id: int) -> ExitStack:
    stack = ExitStack()
    for module in (
        "app.security.decorators.role_authorization",
        "app.security.decorators.auth_context",
        "app.security.decorators.ownership_authorization",
        "app.security.decorators.ownership_filter",
        "app.security.decorators.utils",
    ):
        stack.enter_context(patch(f"{module}.get_authenticated_user_id", return_value=user_id))
    return stack


def test_client_with_mocks_factory(request: Any, mock_rc: Any = None, mock_db: Any = None) -> Any:
    from starlette.testclient import TestClient

    from app.test_app import create_test_app

    return TestClient(create_test_app(mock_rc=mock_rc, mock_db=mock_db))


@pytest.fixture(scope="session")
def test_client_with_mocks(request: Any) -> Any:
    return lambda **kwargs: test_client_with_mocks_factory(request, **kwargs)


@pytest.fixture
def test_client() -> Any:
    from starlette.testclient import TestClient

    from app.test_app import create_test_app

    return TestClient(create_test_app())


@pytest.fixture
def admin_user_token() -> str:
    from app.security import generate_token

    return str(generate_token(11111111))
