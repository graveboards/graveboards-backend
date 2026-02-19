import asyncio
from functools import wraps
from typing import Callable, Any, Awaitable
from inspect import signature, Parameter

from app.database.models import ModelClass
from api.utils import pop_auth_info, prime_query_kwargs, coerce_value


def api_query(model_class: ModelClass, many: bool = False):
    """Decorator for normalizing API query handlers.

    Ensures:
        - Handler is async
        - Auth info is stripped from kwargs
        - Query parameters are normalized for DB layer

    Args:
        model_class:
            Target model for the query.
        many:
            Whether the handler returns multiple results.

    Raises:
        ValueError:
            If applied to a non-async function.
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        if not asyncio.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @api_query")

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Awaitable[Any]:
            pop_auth_info(kwargs)
            prime_query_kwargs(kwargs, many=many)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def coerce_arguments(*params: str, **param_mappings: dict):
    """Decorator for runtime coercion of handler arguments.

    Coerces specified parameters according to their type annotations. Optional mappings
    may be provided to translate specific input values before coercion.

    Args:
        *params:
            Parameter names to coerce.
        **param_mappings:
            Optional value remapping per parameter.

    Raises:
        ValueError:
            If the function is not async or parameter names are invalid.
        TypeError:
            If parameters lack type annotations.
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        if not asyncio.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @coerce_arguments")

        sig = signature(func)
        param_signatures = sig.parameters
        all_params = set(params) | set(param_mappings.keys())

        for name in all_params:
            if name not in param_signatures:
                raise ValueError(f"Parameter '{name}' is not in function '{func.__name__}' signature")

            parameter = param_signatures[name]

            if parameter.annotation is Parameter.empty:
                raise TypeError(f"Parameter '{name}' in '{func.__name__}' must have a type annotation")

        @wraps(func)
        async def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)

            for arg_name in all_params:
                if arg_name not in bound.arguments:
                    continue

                param = param_signatures[arg_name]
                value = bound.arguments[arg_name]
                mapping = param_mappings.get(arg_name)

                if mapping and value in mapping:
                    bound.arguments[arg_name] = mapping[value]
                    continue

                bound.arguments[arg_name] = coerce_value(value, param.annotation, arg_name)

            return await func(*bound.args, **bound.kwargs)

        return wrapper

    return decorator
