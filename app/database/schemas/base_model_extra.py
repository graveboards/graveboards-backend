"""Shared serialization behavior for schema models."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar
from typing import cast as typing_cast

from pydantic.functional_serializers import model_serializer
from pydantic_core import to_jsonable_python

if TYPE_CHECKING:
    from pydantic_core.core_schema import SerializationInfo, SerializerFunctionWrapHandler


class BaseModelExtra:
    """Mixin providing extra serialization options for schema models."""

    model_fields: ClassVar[dict[str, Any]] = {}

    @model_serializer(mode="wrap")
    def serialize(
        self, nxt: SerializerFunctionWrapHandler, info: SerializationInfo
    ) -> dict[str, Any]:
        """Serialize, applying exclusions and optional JSONification of nested values."""
        serialized = nxt(self)
        ctx = info.context or {}

        if exclusions := ctx.get("exclusions"):
            for field in exclusions.get(self.__class__, []):
                serialized.pop(field, None)

        if ctx.get("jsonify_nested"):
            for key, value in serialized.items():
                if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                    serialized[key] = to_jsonable_python(value)

        return typing_cast("dict[str, Any]", serialized)

    @classmethod
    def get_blank_slate(cls) -> dict[str, None]:
        """Build a dictionary of field names mapped to ``None`` for the model."""
        return dict.fromkeys(cls.model_fields)
