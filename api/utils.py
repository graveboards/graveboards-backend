from typing import Iterable, Any, Optional, get_origin, get_args, Union, Literal

from pydantic import BaseModel

from app.database.models import BaseType


def pop_auth_info(
    kwargs: dict[str, Any]
) -> dict[str, Any]:
    return {key: kwargs.pop(key) for key in ("user", "token_info") if key in kwargs}


def prime_query_kwargs(
    kwargs: dict[str, Any],
    many: bool = False
):
    params = {
        "include"
    } if not many else {
        "sorting",
        "include",
        "limit",
        "offset",
        "reversed"
    }

    for key, value in list(kwargs.items()):
        if key in params:
            kwargs["_" + key] = kwargs.pop(key)


def bleach_body(
    body: dict[str, Any],
    whitelisted_keys: Iterable[str] = None,
    blacklisted_keys: Iterable[str] = None
) -> dict[str, Any]:
    whitelist = set(whitelisted_keys) if whitelisted_keys is not None else None
    blacklist = set(blacklisted_keys or ())

    if whitelist is not None:
        if overlap := whitelist & blacklist:
            raise ValueError(f"Keys cannot be both whitelisted and blacklisted: {sorted(overlap)}")

    return {k: v for k, v in body.items() if k in whitelist and k not in blacklist}


def coerce_value(
    value: Any,
    annotation: Any,
    param_name: str
):
    if value is None:
        return None

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is None:
        try:
            return annotation(value)
        except Exception:
            raise TypeError(f"Failed to coerce parameter '{param_name}' to {annotation.__name__}")

    if origin is Union and type(None) in args:
        non_none = next(a for a in args if a is not type(None))
        return coerce_value(value, non_none, param_name)

    if origin is Union:
        last_error = None

        for candidate in args:
            try:
                return coerce_value(value, candidate, param_name)
            except Exception as e:
                last_error = e

        raise TypeError(f"Parameter '{param_name}' does not match any allowed type: {args}") from last_error

    if origin is Literal:
        if value not in args:
            raise TypeError(f"Parameter '{param_name}' must be one of {args}")

        return value

    raise TypeError(f"Unsupported type annotation for parameter '{param_name}': {annotation}")


def build_pydantic_include(
    obj: BaseType | BaseModel,
    include_schema: dict,
    request_include: Optional[dict] = None
):
    defaults = _extract_default_include(include_schema)
    merged = _merge_include(defaults, request_include)
    return _format_include(obj, merged)


def _extract_default_include(include_schema: dict) -> dict:
    if include_schema.get("title").endswith("Shallow"):
        raise RuntimeError("Shallow schemas were not properly resolved")

    result = {}

    if "properties" in include_schema:
        include_schema = include_schema["properties"]

    for name, schema in include_schema.items():
        if schema.get("type") == "boolean":
            result[name] = {
                "__enabled__": schema.get("default", False),
                "__schema__": True
            }
            continue

        if "oneOf" in schema:
            obj_schema = next((s for s in schema["oneOf"] if s.get("type") == "object"), None)
            bool_schema = next((s for s in schema["oneOf"] if s.get("type") == "boolean"), None)

            nested = _extract_default_include(obj_schema) if obj_schema else {}

            result[name] = {
                "__enabled__": bool_schema.get("default", False) if bool_schema else False,
                "__schema__": nested
            }

    return result


def _merge_include(defaults: dict, overrides: Optional[dict] = None) -> dict:
    if overrides is None:
        return defaults

    merged = {}

    for key, default in defaults.items():
        if key not in overrides:
            merged[key] = default
            continue

        override = overrides[key]

        if override is False:
            merged[key] = {
                "__enabled__": False,
                "__schema__": default["__schema__"]
            }

        elif override is True:
            merged[key] = {
                "__enabled__": True,
                "__schema__": default["__schema__"]
            }

        elif isinstance(override, dict):
            merged[key] = {
                "__enabled__": True,
                "__schema__": _merge_include(
                    default["__schema__"],
                    override
                )
            }

    return merged


def _is_collection(obj: BaseType | BaseModel, attr: str) -> bool:
    try:
        value = getattr(obj, attr)
    except AttributeError:
        return False

    if value is None:
        return False

    return isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict))


def _format_include(obj: BaseType | BaseModel, include_tree: dict) -> dict:
    result = {}

    for field, meta in include_tree.items():
        if not meta["__enabled__"]:
            continue

        schema = meta["__schema__"]

        if schema is True:
            result[field] = True
            continue

        if not hasattr(obj, field):
            continue

        value = getattr(obj, field, None)
        if value is None:
            continue

        child_obj = (value[0] if _is_collection(obj, field) and value else value)

        nested = _format_include(child_obj, schema)

        if _is_collection(obj, field):
            result[field] = {"__all__": nested}
        else:
            result[field] = nested

    return result
