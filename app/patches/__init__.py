__all__ = ["OpenAPIURIParserPatched", "ParameterValidatorPatched"]


def __getattr__(name):
    if name == "OpenAPIURIParserPatched":
        from .uri_parsing import OpenAPIURIParserPatched

        return OpenAPIURIParserPatched

    if name == "ParameterValidatorPatched":
        from .parameter import ParameterValidatorPatched

        return ParameterValidatorPatched

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
