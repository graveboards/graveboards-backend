import inspect
from functools import wraps
from typing import Callable, Any, Awaitable, ParamSpec, TypeVar, TYPE_CHECKING
from collections.abc import Sequence

from connexion import request

from app.database.enums import RoleName
from app.config import get_security_enabled
from app.database.models import User
from .utils import get_authenticated_user_id, strip_auth_info, get_value

if TYPE_CHECKING:
    from app.database import PostgresqlDB

P = ParamSpec("P")
T = TypeVar("T")


def ownership_filter(
    resource_user_id_lookup: str = "user_id",
    authorized_user_id_lookup: str = "user",
    bypass_roles: frozenset[RoleName] = frozenset(),
    override: Callable[..., Awaitable[bool]] = None,
    override_kwargs: dict[str, Any] = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Filter handler results to only include items owned by the authenticated user.

    This is a data filtering concern, not a security check. The handler always
    executes regardless of ownership. Use this for list/search endpoints where
    you want users to only see their own results.

    For security enforcement (preventing unauthorized access), use
    ``ownership_authorization`` instead.

    A caller whose role is in ``bypass_roles``, or for whom ``override`` (if
    provided) resolves truthy, skips filtering entirely and receives the
    handler's unfiltered result — mirroring ``ownership_authorization``'s
    admin/override bypass. Do not reach for this on endpoints where filtering
    is the wrong access model to begin with (e.g. a listing that should be
    visible to any caller, filterable only by explicit query params) — leave
    those undecorated instead of bypassing-for-everyone.

    The decorated function must:
        - Be async
        - Accept ``**kwargs``
        - Return a tuple of ``(data, status_code)`` or ``(data, status_code, headers)``
        - Return data as a dict or sequence of dicts

    Args:
        resource_user_id_lookup:
            Key/path used to locate the owner ID on each result item.
        authorized_user_id_lookup:
            Key/path used to locate the authenticated user ID.
        bypass_roles:
            Roles that skip filtering and receive the unfiltered result.
        override:
            Optional async callable resolving to ``True`` to bypass filtering,
            e.g. ``queue_owner_override``. Called with ``db`` and ``**kwargs``
            merged with ``override_kwargs``.
        override_kwargs:
            Extra static kwargs passed to ``override``.

    Raises:
        ValueError:
            If decorator contract is violated.
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        if not inspect.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @ownership_filter")

        sig = inspect.signature(func)
        if not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            raise ValueError(f"Decorated function '{func.__module__}.{func.__name__}' must accept **kwargs to use @ownership_filter")

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if not get_security_enabled():
                return await func(*args, **kwargs)

            try:
                user_id = get_authenticated_user_id(kwargs, authorized_user_id_lookup)
            except KeyError:
                func_path = ".".join((func.__module__, func.__name__))
                raise ValueError(f"Decorated function '{func_path}' must accept **kwargs to use @ownership_filter")

            if bypass_roles or override:
                db: PostgresqlDB = request.state.db

                if bypass_roles:
                    user = await db.get(User, id=user_id, _include={"roles": True})
                    user_roles = {RoleName(role.name) for role in user.roles} if user else set()

                    if user_roles & bypass_roles:
                        strip_auth_info(kwargs)
                        return await func(*args, **kwargs)

                if override:
                    kwargs_for_override = {**kwargs, **(override_kwargs or {})}

                    if await override(db=db, **kwargs_for_override):
                        strip_auth_info(kwargs)
                        return await func(*args, **kwargs)

            strip_auth_info(kwargs)
            result = await func(*args, **kwargs)

            if (
                not isinstance(result, tuple)
                or len(result) < 2
                or not isinstance(result[0], (dict, Sequence))
                or not isinstance(result[1], int)
            ):
                raise ValueError(f"Unexpected result received from function '{func.__name__}', unable to apply ownership filter")

            data, status = result[0], result[1]
            has_headers = len(result) >= 3

            if isinstance(data, dict):
                if get_value(data, resource_user_id_lookup) == user_id:
                    filtered_data = data
                else:
                    filtered_data = {} if isinstance(data, dict) else []
            else:
                filtered_data = [
                    item for item in data
                    if get_value(item, resource_user_id_lookup) == user_id
                ]

            if has_headers:
                return (filtered_data, status) + (result[2],)
            return (filtered_data, status)

        return wrapper

    return decorator
