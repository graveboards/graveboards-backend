"""Decorators for normalizing and coercing API query handler arguments."""

from __future__ import annotations

import inspect
from functools import wraps
from inspect import Parameter, signature
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from api.utils import coerce_value, pop_auth_info, prime_query_kwargs

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from app.database.models import ModelClass

P = ParamSpec("P")
T = TypeVar("T")


def _resolve_annotation(annotation: Any, func_globals: dict[str, Any]) -> Any:
    """Resolve a string annotation to an actual type using the function's globals."""
    if isinstance(annotation, str):
        try:
            return eval(annotation, func_globals)
        except Exception:
            return annotation
    return annotation


def api_query(
    _model_class: ModelClass, many: bool = False
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
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
    ------
        ValueError:
            If applied to a non-async function.
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        if not inspect.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @api_query")

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            auth_info = pop_auth_info(kwargs)
            prime_query_kwargs(kwargs, many=many)

            if getattr(func, "__security_authorization__", False):
                kwargs.update(auth_info)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def coerce_arguments(
    *params: str, **param_mappings: dict
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator for runtime coercion of handler arguments.

    Coerces specified parameters according to their type annotations. Optional mappings
    may be provided to translate specific input values before coercion.

    Args:
        *params:
            Parameter names to coerce.
        **param_mappings:
            Optional value remapping per parameter.

    Raises:
    ------
        ValueError:
            If the function is not async or parameter names are invalid.
        TypeError:
            If parameters lack type annotations.
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        if not inspect.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @coerce_arguments")

        sig = signature(func)
        param_signatures = sig.parameters
        all_params = set(params) | set(param_mappings.keys())

        for name in all_params:
            if name not in param_signatures:
                raise ValueError(
                    f"Parameter '{name}' is not in function '{func.__name__}' signature"
                )

            parameter = param_signatures[name]

            if parameter.annotation is Parameter.empty:
                raise TypeError(
                    f"Parameter '{name}' in '{func.__name__}' must have a type annotation"
                )

        func_globals = func.__globals__
        resolved_annotations: dict[str, Any] = {}
        for name in all_params:
            param = param_signatures[name]
            resolved_annotations[name] = _resolve_annotation(param.annotation, func_globals)

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            bound = sig.bind_partial(*args, **kwargs)

            for arg_name in all_params:
                if arg_name not in bound.arguments:
                    continue

                value = bound.arguments[arg_name]
                mapping = param_mappings.get(arg_name)
                annotation = resolved_annotations[arg_name]

                if mapping and value in mapping:
                    bound.arguments[arg_name] = mapping[value]
                    continue

                bound.arguments[arg_name] = coerce_value(value, annotation, arg_name)

            return await func(*bound.args, **bound.kwargs)

        return wrapper

    return decorator
