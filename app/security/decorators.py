import asyncio
from functools import wraps
from typing import Callable, Any, Awaitable, Iterable
from collections.abc import Sequence

from connexion import request
from connexion.exceptions import Forbidden

from app.database import PostgresqlDB
from app.database.enums import RoleName
from app.config import DISABLE_SECURITY
from app.utils import get_nested_value


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
            db: PostgresqlDB = request.state.db

            if DISABLE_SECURITY:
                return await func(*args, **kwargs)

            try:
                user_id = kwargs["user"]
            except ValueError:
                func_path = ".".join((func.__module__, func.__name__))
                raise KeyError(f"Decorated function '{func_path}' must accept **kwargs to use @role_authorization")

            user = await db.get_user(id=user_id, _loading_options={"roles": True})
            user_roles = {RoleName(role.name) for role in user.roles}
            user_meets_role_requirements = (
                all(required_role in user_roles for required_role in required_roles) if required_roles else
                any(allowed_role in user_roles for allowed_role in one_of) if one_of else False
            )

            override_kwargs_ = {"_db": db, **kwargs, **(override_kwargs or {})}

            if not (
                (override is None and user_meets_role_requirements) or
                (override is not None and (await override(**override_kwargs_) or user_meets_role_requirements))
            ):
                raise Forbidden(detail="User does not have permission to access this resource")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def ownership_authorization(authorized_user_id_lookup: str = "user", resource_user_id_lookup: str = "user_id"):
    def decorator(func: Callable[..., Awaitable[Any]]):
        if not asyncio.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @check_ownership")

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            def check_item_ownership(item_: dict) -> bool:
                try:
                    resource_user_id = get_nested_value(item_, resource_user_id_lookup)
                    return resource_user_id == authorized_user_id
                except KeyError:
                    raise ValueError(f"Invalid data path '{resource_user_id_lookup}'")

            db: PostgresqlDB = request.state.db

            result = await func(*args, **kwargs)

            if DISABLE_SECURITY:
                return result

            if not isinstance(result, tuple) or not isinstance(result[0], (dict, Sequence)) or not isinstance(result[1], int):
                raise ValueError(f"Unexpected result received from function '{func.__name__}', unable to evaluate authorization eligibility")

            data, status = result

            if status >= 400:
                return result

            try:
                authorized_user_id = kwargs[authorized_user_id_lookup]
            except KeyError:
                func_path = ".".join((func.__module__, func.__name__))
                raise ValueError(f"Decorated function '{func_path}' must accept **kwargs to use @ownership_authorization")

            user = await db.get_user(id=authorized_user_id, _loading_options={"roles": True})
            user_roles = {RoleName(role.name) for role in user.roles}

            if any(role is RoleName.ADMIN for role in user_roles):
                return result

            if isinstance(data, dict):
                if not check_item_ownership(data):
                    return {"message": "You are not authorized to access this resource"}, 403
            else:
                for item in data:
                    if not isinstance(item, dict):
                        raise ValueError("All items in list response must be dicts to evaluate ownership")
                    if not check_item_ownership(item):
                        return {"message": "You are not authorized to access this resource"}, 403

            return result

        return wrapper

    return decorator
