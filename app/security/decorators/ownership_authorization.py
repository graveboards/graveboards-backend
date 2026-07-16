import inspect
from functools import wraps
from typing import Callable, Any, Awaitable, ParamSpec, TypeVar, TYPE_CHECKING

from connexion import request
from connexion.exceptions import Forbidden

from app.database.enums import RoleName
from app.config import get_security_enabled
from app.database.models import User
from .utils import get_authenticated_user_id, strip_auth_info, get_value

if TYPE_CHECKING:
    from app.database import PostgresqlDB

P = ParamSpec("P")
T = TypeVar("T")


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
                authorized_user_id = get_authenticated_user_id(kwargs, authorized_user_id_lookup)
            except KeyError:
                func_path = ".".join((func.__module__, func.__name__))
                raise ValueError(f"Decorated function '{func_path}' must accept **kwargs to use @ownership_authorization")

            user = await db.get(User, id=authorized_user_id, _include={"roles": True})
            user_roles = {RoleName(role.name) for role in user.roles}

            if RoleName.ADMIN in user_roles:
                strip_auth_info(kwargs)
                return await func(*args, **kwargs)

            resource_user_id = await _resolve_resource_owner(
                db, kwargs, resource_user_id_lookup, resource_id_lookup, resource_model
            )

            if resource_user_id != authorized_user_id:
                raise Forbidden(detail="You are not authorized to access this resource")

            strip_auth_info(kwargs)
            return await func(*args, **kwargs)

        wrapper.__security_authorization__ = True
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
        return get_value(kwargs, resource_user_id_lookup)
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
            return get_value(resource, resource_user_id_lookup)
        except KeyError:
            raise ValueError(
                f"Resource owner ID '{resource_user_id_lookup}' not found on fetched resource"
            )

    raise ValueError(
        f"Cannot resolve resource owner: '{resource_user_id_lookup}' not in kwargs. "
        f"Provide resource_id_lookup and resource_model to fetch the resource."
    )
