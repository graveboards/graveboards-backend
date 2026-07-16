import inspect
from functools import wraps
from typing import Callable, Any, Awaitable, Iterable, ParamSpec, TypeVar, TYPE_CHECKING
from collections.abc import Sequence

from connexion import request
from connexion.exceptions import Forbidden

from app.database.enums import RoleName
from app.config import get_security_enabled
from app.database.models import User
from app.utils import get_nested_value

if TYPE_CHECKING:
    from app.database import PostgresqlDB

P = ParamSpec("P")
T = TypeVar("T")





def _get_authenticated_user_id(kwargs: dict[str, Any], user_lookup: str = "user") -> int:
    # First, try to get from kwargs (most common case)
    try:
        return get_nested_value(kwargs, user_lookup)
    except KeyError:
        pass

    # Try to get from token_info
    try:
        return kwargs["token_info"]["sub"]
    except KeyError:
        pass

    # If we're in a Connexion request context, try to get user ID from request context
    try:
        from connexion import request
        # Connexion stores user info in request_context after OAuth
        if hasattr(request, "user") and request.user:
            return request.user.get("sub") if isinstance(request.user, dict) else request.user
        if hasattr(request, "token_info") and request.token_info:
            return request.token_info.get("sub")
    except (AttributeError, KeyError):
        pass

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
            if not get_security_enabled():
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
    resource_user_id_lookup: str = "user_id",
    resource_id_lookup: str = None,
    resource_model: type = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator enforcing resource ownership access control.

    Validates that the authenticated user owns the targeted resource BEFORE
    the handler executes. This prevents unauthorized side effects from
    POST/PATCH/DELETE operations.

    The decorated function must:
        - Be async
        - Accept ``**kwargs``

    For single-resource endpoints, the decorator resolves the resource owner
    by first checking kwargs (using ``resource_user_id_lookup``), then falling
    back to fetching the resource from the database (using ``resource_id_lookup``
    to find the resource ID in kwargs and ``resource_model`` to specify the
    SQLAlchemy model).

    Args:
        authorized_user_id_lookup:
            Key/path used to locate the authenticated user ID.
        resource_user_id_lookup:
            Key/path used to locate the resource owner ID. Checked in kwargs
            first, then in the fetched resource.
        resource_id_lookup:
            Optional key in kwargs that contains the resource ID. Required for
            endpoints where the resource owner cannot be resolved from kwargs
            directly (e.g., ``requests/get`` where ``request_id`` is the path
            param but the owner is ``user_id`` on the request record).
        resource_model:
            The SQLAlchemy model class for the resource. Required when
            ``resource_id_lookup`` is set.

    Raises:
        ValueError:
            If decorator contract is violated or ownership cannot be resolved.
        Forbidden:
            If the user does not own the resource.
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        if not inspect.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @ownership_authorization")

        sig = inspect.signature(func)
        if not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            raise ValueError(f"Decorated function '{func.__module__}.{func.__name__}' must accept **kwargs to use @ownership_authorization")

        if resource_id_lookup and resource_model is None:
            raise ValueError(
                f"resource_model is required when resource_id_lookup is set "
                f"for function '{func.__name__}'"
            )

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if not get_security_enabled():
                return await func(*args, **kwargs)

            db: PostgresqlDB = request.state.db

            try:
                authorized_user_id = _get_authenticated_user_id(kwargs, authorized_user_id_lookup)
            except KeyError:
                func_path = ".".join((func.__module__, func.__name__))
                raise ValueError(f"Decorated function '{func_path}' must accept **kwargs to use @ownership_authorization")

            user = await db.get(User, id=authorized_user_id, _include={"roles": True})
            user_roles = {RoleName(role.name) for role in user.roles}

            if RoleName.ADMIN in user_roles:
                _strip_auth_info(kwargs)
                return await func(*args, **kwargs)

            resource_user_id = await _resolve_resource_owner(
                db, kwargs, resource_user_id_lookup, resource_id_lookup, resource_model
            )

            if resource_user_id != authorized_user_id:
                raise Forbidden(detail="You are not authorized to access this resource")

            _strip_auth_info(kwargs)
            return await func(*args, **kwargs)

        wrapper.__security_authorization__ = True
        return wrapper

    return decorator


def ownership_filter(
    resource_user_id_lookup: str = "user_id",
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Filter handler results to only include items owned by the authenticated user.

    This is a data filtering concern, not a security check. The handler always
    executes regardless of ownership. Use this for list/search endpoints where
    you want users to only see their own results.

    For security enforcement (preventing unauthorized access), use
    ``ownership_authorization`` instead.

    The decorated function must:
        - Be async
        - Accept ``**kwargs``
        - Return a tuple of ``(data, status_code)`` or ``(data, status_code, headers)``
        - Return data as a dict or sequence of dicts

    Args:
        resource_user_id_lookup:
            Key/path used to locate the owner ID on each result item.

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
                user_id = _get_authenticated_user_id(kwargs)
            except KeyError:
                func_path = ".".join((func.__module__, func.__name__))
                raise ValueError(f"Decorated function '{func_path}' must accept **kwargs to use @ownership_filter")

            _strip_auth_info(kwargs)
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
                if _get_value(data, resource_user_id_lookup) == user_id:
                    filtered_data = data
                else:
                    filtered_data = {} if isinstance(data, dict) else []
            else:
                filtered_data = [
                    item for item in data
                    if _get_value(item, resource_user_id_lookup) == user_id
                ]

            if has_headers:
                return (filtered_data, status) + (result[2],)
            return (filtered_data, status)

        return wrapper

    return decorator


async def _resolve_resource_owner(
    db: "PostgresqlDB",
    kwargs: dict[str, Any],
    resource_user_id_lookup: str,
    resource_id_lookup: str = None,
    resource_model: type = None,
) -> int:
    """Resolve the resource owner ID for ownership verification.

    Tries to resolve from kwargs first, then falls back to fetching the
    resource from the database.

    Args:
        db:
            Database instance.
        kwargs:
            Request kwargs (path params, query params, etc.).
        resource_user_id_lookup:
            Key/path to locate the owner ID.
        resource_id_lookup:
            Optional key in kwargs that contains the resource ID for fetching.
        resource_model:
            The SQLAlchemy model class for the resource. Required when
            resource_id_lookup is set.

    Returns:
        The owner user ID.

    Raises:
        ValueError:
            If the owner ID cannot be resolved.
    """
    # Try to resolve from kwargs first
    try:
        return _get_value(kwargs, resource_user_id_lookup)
    except KeyError:
        pass

    # Fall back to fetching the resource
    if resource_id_lookup and resource_model is not None:
        try:
            resource_id = kwargs[resource_id_lookup]
        except KeyError:
            raise ValueError(
                f"Cannot resolve resource owner: '{resource_user_id_lookup}' not in "
                f"kwargs and '{resource_id_lookup}' not in kwargs for resource fetching"
            )

        resource = await db.get(resource_model, id=resource_id)
        if resource is None:
            raise ValueError(f"Resource with ID '{resource_id}' not found")

        try:
            return _get_value(resource, resource_user_id_lookup)
        except KeyError:
            raise ValueError(
                f"Resource owner ID '{resource_user_id_lookup}' not found on fetched resource"
            )

    raise ValueError(
        f"Cannot resolve resource owner: '{resource_user_id_lookup}' not in kwargs. "
        f"Provide resource_id_lookup and resource_model to fetch the resource."
    )


def _get_value(obj: Any, path: str) -> Any:
    """Get a value from an object or dict using a dot-separated path.

    Works with both dicts and objects with attributes (SQLAlchemy models,
    Pydantic models, etc.).

    Args:
        obj:
            The object or dict to traverse.
        path:
            Dot-separated path to the value (e.g., "user_id" or "a.b.c").

    Returns:
        The value at the given path.

    Raises:
        KeyError:
            If the path does not exist.
    """
    keys = path.split(".")
    current = obj

    for key in keys:
        if isinstance(current, dict):
            if key in current:
                current = current[key]
            else:
                raise KeyError(f"Key '{key}' not found in {current}")
        else:
            if hasattr(current, key):
                current = getattr(current, key)
            else:
                raise KeyError(f"Attribute '{key}' not found on {type(current).__name__}")

    return current
