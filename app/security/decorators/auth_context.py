import inspect
from functools import wraps
from typing import Callable, Awaitable, ParamSpec, TypeVar

from .utils import get_authenticated_user_id

P = ParamSpec("P")
T = TypeVar("T")


def with_authenticated_user_id(
    kwarg_name: str = "_caller_user_id",
    authorized_user_id_lookup: str = "user",
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Pass the authenticated caller's user ID into the handler, enforcing nothing.

    Unlike ``ownership_authorization``/``ownership_filter``, this performs no access
    control - it just makes the caller's identity available (as ``kwarg_name``) to
    handlers that need it for their own data-shaping logic (e.g. a queue listing that
    is public to everyone but should additionally surface the caller's own unlisted/
    private queues). Resolves to ``None`` if no authenticated user is present.

    Must be applied *outside* ``@api_query`` so it can read ``kwargs["user"]`` before
    that decorator strips it. The decorated function must pop ``kwarg_name`` out of
    ``kwargs`` before passing ``**kwargs`` through to a DB filter_by-style call.
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        if not inspect.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @with_authenticated_user_id")

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                user_id = get_authenticated_user_id(kwargs, authorized_user_id_lookup)
            except KeyError:
                user_id = None

            kwargs[kwarg_name] = user_id

            return await func(*args, **kwargs)

        return wrapper

    return decorator
