from typing import Any, Iterable

from pydantic.functional_serializers import model_serializer
from pydantic_core.core_schema import SerializerFunctionWrapHandler, SerializationInfo
from pydantic_core import to_jsonable_python


class BaseModelExtra:
    model_fields = ...

    @model_serializer(mode="wrap")
    def serialize(self, nxt: SerializerFunctionWrapHandler, info: SerializationInfo) -> dict[str, Any]:
        serialized = nxt(self)
        ctx = info.context or {}

        if exclusions := ctx.get("exclusions"):
            for field in exclusions.get(self.__class__, []):
                serialized.pop(field, None)

        if ctx.get("jsonify_nested"):
            for key, value in serialized.items():
                if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                    serialized[key] = to_jsonable_python(value)

        return serialized

    @classmethod
    def get_blank_slate(cls) -> dict[str, None]:
        return {field: None for field in cls.model_fields}
