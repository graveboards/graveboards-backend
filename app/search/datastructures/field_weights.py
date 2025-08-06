import struct
from collections import defaultdict
from enum import IntFlag, auto
from typing import Generator, Optional, Annotated

from pydantic.main import BaseModel
from pydantic.fields import Field
from pydantic.functional_validators import model_validator
from pydantic.config import ConfigDict

from app.exceptions import AllValuesNullError
from app.search.enums import Scope, ModelField, SearchableFieldCategory

SCOPE_CATEGORIES_MAPPING = {
    Scope.BEATMAPS: [SearchableFieldCategory.BEATMAP],
    Scope.BEATMAPSETS: [SearchableFieldCategory.BEATMAP, SearchableFieldCategory.BEATMAPSET],
    Scope.SCORES: ...,
    Scope.QUEUES: [SearchableFieldCategory.BEATMAP, SearchableFieldCategory.BEATMAPSET, SearchableFieldCategory.QUEUE],
    Scope.REQUESTS: [SearchableFieldCategory.BEATMAP, SearchableFieldCategory.BEATMAPSET, SearchableFieldCategory.REQUEST]
}

CATEGORY_MODEL_FIELDS_MAPPING = {
    SearchableFieldCategory.BEATMAP: {
        "version": ModelField.BEATMAPSNAPSHOT__VERSION
    },
    SearchableFieldCategory.BEATMAPSET: {
        "title": ModelField.BEATMAPSETSNAPSHOT__TITLE,
        "title_unicode": ModelField.BEATMAPSETSNAPSHOT__TITLE_UNICODE,
        "artist": ModelField.BEATMAPSETSNAPSHOT__ARTIST,
        "artist_unicode": ModelField.BEATMAPSETSNAPSHOT__ARTIST_UNICODE,
        "creator": ModelField.BEATMAPSETSNAPSHOT__CREATOR,
        "source": ModelField.BEATMAPSETSNAPSHOT__SOURCE,
        "tags": ModelField.BEATMAPSETSNAPSHOT__TAGS,
        "description": ModelField.BEATMAPSETSNAPSHOT__DESCRIPTION__DESCRIPTION
    },
    SearchableFieldCategory.QUEUE: {
        "name": ModelField.QUEUE__NAME,
        "description": ModelField.QUEUE__DESCRIPTION
    },
    SearchableFieldCategory.REQUEST: {
        "comment": ModelField.REQUEST__COMMENT
    }
}

CATEGORY_FIELD_GROUPS_MAPPING = {
    SearchableFieldCategory.BEATMAPSET: {
        "title": {"title", "title_unicode"},
        "artist": {"artist", "artist_unicode"}
    }
}


class BeatmapFieldWeights(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Optional[Annotated[int, Field(ge=-128, le=127)]] = 2


class BeatmapsetFieldWeights(BaseModel):
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
    model_config = ConfigDict(extra="forbid")

    name: Optional[Annotated[int, Field(ge=-128, le=127)]] = 6
    description: Optional[Annotated[int, Field(ge=-128, le=127)]] = 0


class RequestFieldWeights(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: Optional[Annotated[int, Field(ge=-128, le=127)]] = 0


class FieldWeights(BaseModel):
    model_config = ConfigDict(extra="forbid")

    beatmap: BeatmapFieldWeights = Field(default_factory=BeatmapFieldWeights)
    beatmapset: BeatmapsetFieldWeights = Field(default_factory=BeatmapsetFieldWeights)
    queue: QueueFieldWeights = Field(default_factory=QueueFieldWeights)
    request: RequestFieldWeights = Field(default_factory=RequestFieldWeights)

    @model_validator(mode="before")
    @classmethod
    def handle_disable_shorthand(cls, values):
        for key, value in values.items():
            if value is None and key in cls.model_fields:
                model_class = cls.model_fields[key].annotation
                values[key] = model_class(**{f: None for f in model_class.model_fields})

        return values

    def validate_against_scope(self, scope: Scope):
        for category_name, model in self:
            category = SearchableFieldCategory.from_name(category_name)

            if category not in SCOPE_CATEGORIES_MAPPING[scope]:
                continue

            if any(getattr(model, field) is not None for field in model.model_fields):
                return

        raise AllValuesNullError("FieldWeights")

    def serialize(self, scope: Scope) -> bytes:
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


_DEFAULTS = FieldWeights().model_dump()

FieldWeightFieldFlag = IntFlag(
    "FieldWeightFieldFlag",
    {
        f"{category_name}__{field}": auto()
        for category_name, defaults in _DEFAULTS.items()
        for field in defaults.keys()
    },
)
