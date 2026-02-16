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
    def __call__(
        self,
        obj: Any,
        *,
        autoflush: bool = True,
    ) -> AsyncContextManager[AsyncSession]: ...


class DbSessionResolver(SessionResolver):
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
    return obj.session(autoflush=autoflush)


def _enforce_autoflush(
    session: AsyncSession,
    autoflush_allowed: bool,
    func: Callable[P, Awaitable[T] | AsyncIterator[T]]
):
    if not autoflush_allowed and session.autoflush:
        raise RuntimeError(f"{func.__name__} requires autoflush=False but received session with autoflush=True.")
