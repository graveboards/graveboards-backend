import struct
from enum import IntFlag, auto
from typing import Literal, Optional, Annotated

from pydantic.main import BaseModel
from pydantic.functional_validators import model_validator
from pydantic.fields import Field
from pydantic.config import ConfigDict

from app.exceptions import AllValuesNullError

PatternName = Literal["exact", "prefix", "suffix", "substring"]


class PatternMultipliers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exact: Optional[Annotated[int, Field(ge=-128, le=127)]] = 5
    prefix: Optional[Annotated[int, Field(ge=-128, le=127)]] = 4
    suffix: Optional[Annotated[int, Field(ge=-128, le=127)]] = 3
    substring: Optional[Annotated[int, Field(ge=-128, le=127)]] = 2

    @model_validator(mode="after")
    def at_least_one_not_null(self):
        if any(getattr(self, field) is not None for field in self.model_fields):
            return self

        raise AllValuesNullError("pattern_multipliers")

    def get_patterns(self, term: str) -> list[tuple[PatternName, str, Optional[int]]]:
        return [
            ("exact", term, self.exact),
            ("prefix", f"{term}%", self.prefix),
            ("suffix", f"%{term}", self.suffix),
            ("substring", f"%{term}%", self.substring),
        ]

    def serialize(self) -> bytes:
        presence = 0
        null_presence = 0
        chunks = []

        for match_type, default_value in _DEFAULTS.items():
            value = getattr(self, match_type)

            if value != default_value:
                if value is not None:
                    presence |= PatternMultiplierFieldFlag[match_type]
                    chunks.append(struct.pack("!b", value))
                else:
                    null_presence |= PatternMultiplierFieldFlag[match_type]

        presence_byte = struct.pack("!B", presence)
        null_presence_byte = struct.pack("!B", null_presence)

        return presence_byte + null_presence_byte + b"".join(chunks)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["PatternMultipliers", int]:
        presence, null_presence = struct.unpack_from("!BB", data, offset)
        offset += 2
        values = {}

        for flag in PatternMultiplierFieldFlag:
            if presence & flag:
                values[flag.name] = struct.unpack_from("!b", data, offset)[0]
                offset += 1
            elif null_presence & flag:
                values[flag.name] = None

        return cls(**values), offset


_DEFAULTS = PatternMultipliers().model_dump()

PatternMultiplierFieldFlag = IntFlag("PatternMultiplierFieldFlag", {field: auto() for field in PatternMultipliers.model_fields.keys()})
