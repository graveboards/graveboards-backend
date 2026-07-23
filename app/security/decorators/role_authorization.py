import inspect
from functools import wraps
from typing import Callable, Awaitable, Iterable, ParamSpec, TypeVar, TYPE_CHECKING, Any

from connexion import request
from connexion.exceptions import Forbidden

from app.database.enums import RoleName
from app.database.roles import get_user_roles
from .utils import get_authenticated_user_id, strip_auth_info

if TYPE_CHECKING:
    from app.database import PostgresqlDB

P = ParamSpec("P")
T = TypeVar("T")


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
            db: PostgresqlDB = request.state.db

            try:
                user_id = get_authenticated_user_id(kwargs)
            except KeyError:
                func_path = ".".join((func.__module__, func.__name__))
                raise ValueError(f"Decorated function '{func_path}' must accept **kwargs to use @role_authorization")

            kwargs["user"] = user_id
            user_roles = await get_user_roles(db, user_id)
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

            strip_auth_info(kwargs)
            return await func(*args, **kwargs)

        wrapper.__security_authorization__ = True
        return wrapper

    return decorator
