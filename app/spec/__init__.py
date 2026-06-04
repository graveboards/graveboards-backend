__all__ = ["load_spec", "get_filter_schema", "get_include_schema"]


def __getattr__(name):
    if name == "load_spec":
        from .load import load_spec

        return load_spec

    if name in {"get_filter_schema", "get_include_schema"}:
        from . import schema

        return getattr(schema, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
