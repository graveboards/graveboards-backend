import inspect
from functools import wraps
from typing import Callable, Any, Awaitable, Iterable, ParamSpec, TypeVar, TYPE_CHECKING
from collections.abc import Sequence

from connexion import request
from connexion.exceptions import Forbidden

from app.database.enums import RoleName
from app.config import DISABLE_SECURITY
from app.database.models import User
from app.utils import get_nested_value

if TYPE_CHECKING:
    from app.database import PostgresqlDB

P = ParamSpec("P")
T = TypeVar("T")


def _get_authenticated_user_id(kwargs: dict[str, Any], user_lookup: str = "user") -> int:
    try:
        return get_nested_value(kwargs, user_lookup)
    except KeyError:
        pass

    try:
        return kwargs["token_info"]["sub"]
    except KeyError:
        raise KeyError(user_lookup)


def _strip_auth_info(kwargs: dict[str, Any]) -> None:
    kwargs.pop("user", None)
    kwargs.pop("token_info", None)


def role_authorization(
    *required_roles: RoleName,
    one_of: Iterable[RoleName] = None,
    override: Callable[..., Awaitable[bool]] = None,
    override_kwargs: dict[str, Any] = None
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator enforcing role-based access control on endpoints.

    Supports:
        - Requiring all specified roles
        - Requiring at least one role (``one_of``)
        - Optional override callback for dynamic authorization logic

    The decorated function must:
        - Be async
        - Accept ``**kwargs``
        - Provide the authenticated user ID via ``kwargs["user"]``

    Args:
        *required_roles:
            Roles the user must possess (all required).
        one_of:
            Iterable of roles where at least one must be present.
        override:
            Optional async callable returning ``True`` to allow access.
        override_kwargs:
            Additional keyword arguments passed to override.

    Raises:
        ValueError:
            For invalid decorator usage or missing parameters.
        Forbidden:
            If authorization fails.
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        if not inspect.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @role_authorization")

        sig = inspect.signature(func)
        if not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            raise ValueError(f"Decorated function '{func.__module__}.{func.__name__}' must accept **kwargs to use @role_authorization")

        if required_roles and one_of is not None:
            raise ValueError("Arg(s) 'required_roles' and kwarg 'one_of' are mutually exclusive")
        elif not required_roles and one_of is None:
            raise ValueError("Must provide either 'required_roles' arg(s) or 'one_of' kwarg")

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if DISABLE_SECURITY:
                return await func(*args, **kwargs)

            db: PostgresqlDB = request.state.db

            try:
                user_id = _get_authenticated_user_id(kwargs)
            except KeyError:
                func_path = ".".join((func.__module__, func.__name__))
                raise ValueError(f"Decorated function '{func_path}' must accept **kwargs to use @role_authorization")

            kwargs["user"] = user_id
            user = await db.get(User, id=user_id, _include={"roles": True})
            user_roles = {RoleName(role.name) for role in user.roles}
            user_meets_role_requirements = (
                all(role in user_roles for role in required_roles)
                if required_roles
                else any(role in user_roles for role in one_of)
            )

            override_kwargs_ = {"db": db, **kwargs, **(override_kwargs or {})}

            authorized = (
                user_meets_role_requirements
                if override is None
                else (
                    user_meets_role_requirements
                    or await override(**override_kwargs_)
                )
            )

            if not authorized:
                raise Forbidden(detail="You are not authorized to access this resource")

            _strip_auth_info(kwargs)
            return await func(*args, **kwargs)

        wrapper.__security_authorization__ = True
        return wrapper

    return decorator


def ownership_authorization(
    authorized_user_id_lookup: str = "user",
    resource_user_id_lookup: str = "user_id"
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator enforcing resource ownership access control.

    Ensures the authenticated user matches the owner of the returned resource(s), unless
    the user has an administrative role.

    The decorated function must:
        - Be async
        - Accept ``**kwargs``
        - Return a tuple of ``(data, status_code)`` or ``(data, status_code, headers)``
        - Return data as a dict or sequence of dicts

    Args:
        authorized_user_id_lookup:
            Key/path used to locate the authenticated user ID.
        resource_user_id_lookup:
            Key/path used to locate the resource owner ID.

    Raises:
        ValueError:
            If decorator contract is violated.
        Forbidden:
            If ownership validation fails.
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        if not inspect.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @check_ownership")

        sig = inspect.signature(func)
        if not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            raise ValueError(f"Decorated function '{func.__module__}.{func.__name__}' must accept **kwargs to use @ownership_authorization")

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if DISABLE_SECURITY:
                return await func(*args, **kwargs)

            db: PostgresqlDB = request.state.db

            try:
                authorized_user_id = _get_authenticated_user_id(kwargs, authorized_user_id_lookup)
            except KeyError:
                func_path = ".".join((func.__module__, func.__name__))
                raise ValueError(f"Decorated function '{func_path}' must accept **kwargs to use @ownership_authorization")

            _strip_auth_info(kwargs)
            result = await func(*args, **kwargs)

            if (
                not isinstance(result, tuple)
                or len(result) < 2
                or not isinstance(result[0], (dict, Sequence))
                or not isinstance(result[1], int)
            ):
                raise ValueError(f"Unexpected result received from function '{func.__name__}', unable to evaluate authorization eligibility")

            data, status = result[0], result[1]
            has_headers = len(result) >= 3

            if status >= 400:
                return result

            user = await db.get(User, id=authorized_user_id, _include={"roles": True})
            user_roles = {RoleName(role.name) for role in user.roles}

            if RoleName.ADMIN in user_roles:
                return result

            def check_item_ownership(item_: dict) -> bool:
                try:
                    resource_user_id = get_nested_value(item_, resource_user_id_lookup)
                    return resource_user_id == authorized_user_id
                except KeyError:
                    raise ValueError(f"Invalid data path '{resource_user_id_lookup}'")

            if isinstance(data, dict):
                if not check_item_ownership(data):
                    raise Forbidden(detail="You are not authorized to access this resource")
            else:
                for item in data:
                    if not isinstance(item, dict):
                        raise ValueError(f"Invalid result received from function '{func.__name__}', all items in response must be dicts to evaluate ownership")

                    if not check_item_ownership(item):
                        raise Forbidden(detail="You are not authorized to access this resource")

            if has_headers:
                return (data, status) + (result[2],)
            return (data, status)

        wrapper.__security_authorization__ = True
        return wrapper

    return decorator
