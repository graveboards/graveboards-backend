import inspect
from functools import wraps
from typing import Callable, Awaitable, Any, AsyncIterator, ParamSpec, TypeVar, AsyncContextManager, Protocol
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.logging import get_logger, log_stack_warning
from app.database.models import ModelClass
from .protocol import DatabaseProtocol

P = ParamSpec("P")
T = TypeVar("T")
logger = get_logger(__name__)

_active_session: ContextVar[AsyncSession | None] = ContextVar(
    "active_session",
    default=None,
)


def session_manager(
    session_resolver: SessionResolver = None,
    autoflush_allowed: bool = True
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Manage ``AsyncSession`` lifecycle for coroutine-based CRUD operations.

    This decorator ensures that a valid session is available for the wrapped method.

    Session resolution order:
        1. Explicitly passed ``session``
        2. Currently active ``ContextVar`` session
        3. Newly created session via ``session_resolver``

    The active session is stored in a ``ContextVar`` to allow safe nested CRUD calls
    without reopening sessions.

    Args:
        session_resolver:
            Callable that returns an ``AsyncSession`` context manager. Defaults to the
            object's `session()` method.
        autoflush_allowed:
            If False, enforces that the session has autoflush disabled.

    Returns:
        A wrapped async function that guarantees session availability.

    Raises:
        RuntimeError:
            If autoflush constraints are violated.
    """
    if session_resolver is None:
        session_resolver = _default_session_resolver

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> T:
            passed_session = kwargs.get("session")
            current_session = _active_session.get()

            if passed_session is not None:
                _enforce_autoflush(passed_session, autoflush_allowed, func)
                token = _active_session.set(passed_session)

                try:
                    return await func(self, *args, **kwargs)
                finally:
                    _active_session.reset(token)

            if current_session is not None:
                _enforce_autoflush(current_session, autoflush_allowed, func)
                stack = inspect.stack()
                log_stack_warning(logger, stack, f"Func '{func.__name__}' called w/o session inside active session context")
                kwargs["session"] = current_session
                return await func(self, *args, **kwargs)

            async with session_resolver(self, autoflush=autoflush_allowed) as session:
                _enforce_autoflush(session, autoflush_allowed, func)
                token = _active_session.set(session)

                try:
                    kwargs["session"] = session
                    return await func(self, *args, **kwargs)
                finally:
                    _active_session.reset(token)

        return wrapper

    return decorator


def session_manager_stream(
    session_resolver: Callable[[Any], AsyncContextManager[Any]] = None,
    autoflush_allowed: bool = True
) -> Callable[[Callable[P, AsyncIterator[T]]], Callable[P, AsyncIterator[T]]]:
    """Manage ``AsyncSession`` lifecycle for async generator methods.

    Mirrors ``session_manager`` but supports async iterators. Ensures that a valid
    session remains active for the full duration of the stream.

    Session resolution order:
        1. Explicitly passed ``session``
        2. Currently active ``ContextVar`` session
        3. Newly created session via ``session_resolver``

    Args:
        session_resolver:
            Callable that returns an AsyncSession context manager. Defaults to the
            object's `session()` method.
        autoflush_allowed:
            If False, enforces that the session has autoflush disabled.

    Returns:
        A wrapped async generator function with managed session scope.

    Raises:
        RuntimeError:
            If autoflush constraints are violated.
    """
    if session_resolver is None:
        session_resolver = _default_session_resolver

    def decorator(func: Callable[P, AsyncIterator[T]]) -> Callable[P, AsyncIterator[T]]:
        @wraps(func)
        async def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> AsyncIterator[T]:
            passed_session = kwargs.get("session")
            current_session = _active_session.get()

            if passed_session is not None:
                _enforce_autoflush(passed_session, autoflush_allowed, func)
                token = _active_session.set(passed_session)

                try:
                    async for item in func(self, *args, **kwargs):
                        yield item
                finally:
                    _active_session.reset(token)

                return

            if current_session is not None:
                _enforce_autoflush(current_session, autoflush_allowed, func)
                stack = inspect.stack()
                log_stack_warning(logger, stack, f"Func '{func.__name__}' called w/o session inside active session context")
                kwargs["session"] = current_session

                async for item in func(self, *args, **kwargs):
                    yield item

                return

            async with session_resolver(self, autoflush=autoflush_allowed) as session:
                _enforce_autoflush(session, autoflush_allowed, func)
                token = _active_session.set(session)

                try:
                    kwargs["session"] = session

                    async for item in func(self, *args, **kwargs):
                        yield item
                finally:
                    _active_session.reset(token)

        return wrapper

    return decorator


def ensure_required(many: bool = False) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Validate presence of required model columns before execution.

    This decorator checks that all required columns defined on the model are present in
    the provided input data.

    Args:
        many:
            If False, validates keyword arguments for a single instance. If True,
            validates each dictionary in positional arguments (used for bulk creation).

    Returns:
        A wrapped async function that enforces required column validation.

    Raises:
        ValueError:
            If required columns are missing.
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(model_class: ModelClass, session: AsyncSession, *args: P.args, **kwargs: P.kwargs) -> T:
            required_columns = model_class.required_columns

            def get_missing(d_: dict) -> list[str]:
                return [col for col in required_columns if col not in d_]

            if not many:
                missing_columns = get_missing(kwargs)

                if missing_columns:
                    raise ValueError(f"Missing required columns: {", ".join(missing_columns)}")
            else:
                for i, d in enumerate(args):
                    missing_columns = get_missing(d)

                    if missing_columns:
                        raise ValueError(f"Missing required columns at index {i}: {", ".join(missing_columns)}")

            return await func(model_class, session, *args, **kwargs)

        return wrapper

    return decorator


class SessionResolver(Protocol):
    """Protocol for resolving an AsyncSession context manager.

    Implementations must return an async context manager that yields an ``AsyncSession``
    instance. This abstraction allows CRUD decorators to remain decoupled from specific
    database wiring strategies.
    """
    def __call__(
        self,
        obj: Any,
        *,
        autoflush: bool = True,
    ) -> AsyncContextManager[AsyncSession]: ...


class DbSessionResolver(SessionResolver):
    """SessionResolver implementation that delegates to `obj.db.session()`.

    Intended for use when the database handle is stored on an attribute
    named `db` rather than exposed directly via `session()`.
    """
    def __call__(
        self,
        obj: Any,
        *,
        autoflush: bool = True
    ) -> AsyncContextManager[AsyncSession]:
        return obj.db.session(autoflush=autoflush)


db_session_resolver = DbSessionResolver()


def _default_session_resolver(
    obj: DatabaseProtocol,
    *,
    autoflush: bool = True
) -> AsyncContextManager[AsyncSession]:
    """Default strategy for resolving a session from a ``DatabaseProtocol``.

    Delegates to `obj.session()`.

    Args:
        obj:
            Object implementing the ``DatabaseProtocol`` interface.
        autoflush:
            Whether the resolved session should enable autoflush.

    Returns:
        An async context manager yielding an ``AsyncSession``.
    """
    return obj.session(autoflush=autoflush)


def _enforce_autoflush(
    session: AsyncSession,
    autoflush_allowed: bool,
    func: Callable[P, Awaitable[T] | AsyncIterator[T]]
):
    """Enforce autoflush policy for a wrapped CRUD operation.

    Args:
        session:
            Active ``AsyncSession``.
        autoflush_allowed:
            Whether autoflush is permitted for this operation.
        func:
            The wrapped function (used for error context).

    Raises:
        RuntimeError:
            If autoflush is enabled when disallowed.
    """
    if not autoflush_allowed and session.autoflush:
        raise RuntimeError(f"{func.__name__} requires autoflush=False but received session with autoflush=True.")
