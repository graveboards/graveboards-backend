from typing import Any

from app.utils import get_nested_value


def get_authenticated_user_id(kwargs: dict[str, Any], user_lookup: str = "user") -> int:
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


def strip_auth_info(kwargs: dict[str, Any]) -> None:
    kwargs.pop("user", None)
    kwargs.pop("token_info", None)


def get_value(obj: Any, path: str) -> Any:
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
