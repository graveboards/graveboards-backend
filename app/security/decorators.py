import asyncio
from functools import wraps
from typing import Callable, Any, Awaitable, Iterable

from connexion import request
from connexion.exceptions import Forbidden

from app.database import PostgresqlDB
from app.database.enums import RoleName
from app.config import DISABLE_SECURITY


def role_authorization(*required_roles: RoleName, one_of: Iterable[RoleName] = None, override: Callable[..., Awaitable[bool]] = None, override_kwargs: dict[str, Any] = None):
    def decorator(func: Callable[..., Awaitable[Any]]):
        if not asyncio.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @role_authorization")

        if required_roles and one_of is not None:
            raise ValueError("Arg(s) 'required_roles' and kwarg 'one_of' are mutually exclusive")
        elif not required_roles and one_of is None:
            raise ValueError("Must provide either 'required_roles' arg(s) or 'one_of' kwarg")

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Awaitable[Any]:
            if DISABLE_SECURITY:
                return await func(*args, **kwargs)

            db: PostgresqlDB = request.state.db

            try:
                user_id = kwargs["user"]
            except KeyError:
                func_path = ".".join((func.__module__, func.__name__))
                raise KeyError(f"Decorated function '{func_path}' must accept **kwargs to use @role_authorization")

            user_role_names = {RoleName(role.name) for role in (await db.get_user(id=user_id, _auto_eager_loads={"roles"})).roles}
            user_meets_role_requirements = (
                all(required_role in user_role_names for required_role in required_roles) if required_roles else
                any(allowed_role in user_role_names for allowed_role in one_of) if one_of else False
            )

            override_kwargs_ = {"_db": db, **kwargs, **(override_kwargs if override_kwargs else {})}

            if not (
                (override is None and user_meets_role_requirements) or
                (override is not None and (await override(**override_kwargs_) or user_meets_role_requirements))
            ):
                raise Forbidden(detail="User does not have permission to access this resource")

            return await func(*args, **kwargs)

        return wrapper

    return decorator
