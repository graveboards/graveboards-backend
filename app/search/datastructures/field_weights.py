import struct
from collections import defaultdict
from enum import IntFlag, auto
from typing import Generator, Optional, Annotated

from pydantic.main import BaseModel
from pydantic.fields import Field
from pydantic.functional_validators import model_validator
from pydantic.config import ConfigDict

from app.exceptions import AllValuesNullError
from app.search.enums import Scope, SearchableFieldCategory
from app.search.mappings import SCOPE_CATEGORIES_MAPPING


class BeatmapFieldWeights(BaseModel):
    """Defines per-field scoring weights for the corresponding category.

    Weights must be within signed byte range (``-128`` to ``127``). ``None`` disables
    scoring for the field.
    """
    model_config = ConfigDict(extra="forbid")

    version: Optional[Annotated[int, Field(ge=-128, le=127)]] = 2


class BeatmapsetFieldWeights(BaseModel):
    """Defines per-field scoring weights for the corresponding category.

    Weights must be within signed byte range (``-128`` to ``127``). ``None`` disables
    scoring for the field.
    """
    model_config = ConfigDict(extra="forbid")

    title: Optional[Annotated[int, Field(ge=-128, le=127)]] = 5
    title_unicode: Optional[Annotated[int, Field(ge=-128, le=127)]] = 5
    artist: Optional[Annotated[int, Field(ge=-128, le=127)]] = 4
    artist_unicode: Optional[Annotated[int, Field(ge=-128, le=127)]] = 4
    creator: Optional[Annotated[int, Field(ge=-128, le=127)]] = 3
    source: Optional[Annotated[int, Field(ge=-128, le=127)]] = 2
    tags: Optional[Annotated[int, Field(ge=-128, le=127)]] = 1
    description: Optional[Annotated[int, Field(ge=-128, le=127)]] = 0


class QueueFieldWeights(BaseModel):
    """Defines per-field scoring weights for the corresponding category.

    Weights must be within signed byte range (``-128`` to ``127``). ``None`` disables
    scoring for the field.
    """
    model_config = ConfigDict(extra="forbid")

    name: Optional[Annotated[int, Field(ge=-128, le=127)]] = 6
    description: Optional[Annotated[int, Field(ge=-128, le=127)]] = 0


class RequestFieldWeights(BaseModel):
    """Defines per-field scoring weights for the corresponding category.

    Weights must be within signed byte range (``-128`` to ``127``). ``None`` disables
    scoring for the field.
    """
    model_config = ConfigDict(extra="forbid")

    comment: Optional[Annotated[int, Field(ge=-128, le=127)]] = 0


class FieldWeights(BaseModel):
    """Aggregated field weighting configuration across categories.

    Controls per-field contribution to relevance scoring. Supports compact bitmask-based
    serialization.
    """
    model_config = ConfigDict(extra="forbid")

    beatmap: BeatmapFieldWeights = Field(default_factory=BeatmapFieldWeights)
    beatmapset: BeatmapsetFieldWeights = Field(default_factory=BeatmapsetFieldWeights)
    queue: QueueFieldWeights = Field(default_factory=QueueFieldWeights)
    request: RequestFieldWeights = Field(default_factory=RequestFieldWeights)

    @model_validator(mode="before")
    @classmethod
    def handle_disable_shorthand(cls, values):
        """Expand shorthand ``None`` category values into explicit null fields.

        If a category is explicitly set to ``None``, all of its fields are expanded into
        a dictionary where each field is set to ``None``, disabling the category.

        Args:
            values:
                Raw input values for model initialization.

        Returns:
            Updated values dictionary with expanded category definitions.
        """
        for key, value in values.items():
            if value is None and key in cls.model_fields:
                model_class = cls.model_fields[key].annotation
                values[key] = model_class(**{f: None for f in model_class.model_fields})

        return values

    def validate_against_scope(self, scope: Scope):
        """Ensure at least one applicable field weight is enabled for the scope.

        Only categories mapped to the provided scope are considered. At least one field
        within the applicable categories must have a non-``None`` weight.

        Args:
            scope:
                Search scope used to determine applicable categories.

        Raises:
            AllValuesNullError:
                If no effective field weights are enabled for the given scope.
        """
        for category_name, model in self:
            category = SearchableFieldCategory.from_name(category_name)

            if category not in SCOPE_CATEGORIES_MAPPING[scope]:
                continue

            if any(getattr(model, field) is not None for field in model.model_fields):
                return

        raise AllValuesNullError("field_weights")

    def serialize(self, scope: Scope) -> bytes:
        """Serialize non-default field weights into compact binary format.

        Serialization behavior:
            - Only fields relevant to the provided scope are considered.
            - Fields that differ from their default value are encoded.
            - Presence and null-state are encoded using bit flags.
            - Non-null values are stored as signed bytes.

        Args:
            scope:
                Search scope determining applicable categories.

        Returns:
            A bytes object containing the serialized field weights.
        """
        presence = 0
        null_presence = 0
        chunks = []

        def iter_fields() -> Generator[tuple[str, int], None, None]:
            for category_name, defaults in _DEFAULTS.items():
                if SearchableFieldCategory.from_name(category_name) not in SCOPE_CATEGORIES_MAPPING[scope]:
                    continue

                model = getattr(self, category_name)

                for field, default_value in defaults.items():
                    value_ = getattr(model, field)

                    if value_ != default_value:
                        yield f"{category_name}__{field}", value_

        for flat_field, value in iter_fields():
            if value is not None:
                presence |= FieldWeightFieldFlag[flat_field]
                chunks.append(struct.pack("!b", value))
            else:
                null_presence |= FieldWeightFieldFlag[flat_field]

        presence_byte = struct.pack("!H", presence)
        null_presence_byte = struct.pack("!H", null_presence)

        return presence_byte + null_presence_byte + b"".join(chunks)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["FieldWeights", int]:
        """Deserialize binary data into a ``FieldWeights`` instance.

        Args:
            data:
                Serialized byte sequence.
            offset:
                Starting offset within the byte sequence.

        Returns:
            A tuple containing:
                - The reconstructed ``FieldWeights`` instance
                - The updated byte offset
        """
        presence, null_presence = struct.unpack_from("!HH", data, offset)
        offset += 4
        values = defaultdict(dict)

        for flag in FieldWeightFieldFlag:
            category_name, field = flag.name.split("__")

            if presence & flag:
                values[category_name][field] = struct.unpack_from("!b", data, offset)[0]
                offset += 1
            elif null_presence & flag:
                values[category_name][field] = None

        return cls(**values), offset


# Default field weight configuration used for diff-based serialization.
_DEFAULTS = FieldWeights().model_dump()

FieldWeightFieldFlag = IntFlag(
    "FieldWeightFieldFlag",
    {
        f"{category_name}__{field}": auto()
        for category_name, defaults in _DEFAULTS.items()
        for field in defaults.keys()
    },
)
"""
Bitmask flags representing individual field weights.

Each flag corresponds to a flattened "category__field" identifier and is used to encode 
presence and null-state information during binary serialization.
"""
