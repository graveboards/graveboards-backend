import struct
from enum import IntFlag, auto
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, model_validator
from pydantic.config import ConfigDict

from app.exceptions import AllValuesNullError

PatternName = Literal["exact", "prefix", "suffix", "substring"]


class PatternMultipliers(BaseModel):
    """Scoring multipliers for different text match patterns.

    Supports `exact`, `prefix`, `suffix`, and `substring` matches.

    Multipliers must be within signed byte range (``-128`` to ``127``). ``None``
    disables scoring for the pattern. However, at least one multiplier must be enabled.
    """

    model_config = ConfigDict(extra="forbid")

    exact: Annotated[int, Field(ge=-128, le=127)] | None = 5
    prefix: Annotated[int, Field(ge=-128, le=127)] | None = 4
    suffix: Annotated[int, Field(ge=-128, le=127)] | None = 3
    substring: Annotated[int, Field(ge=-128, le=127)] | None = 2

    @model_validator(mode="after")
    def at_least_one_not_null(self) -> Self:
        """Ensure at least one multiplier is enabled.

        Returns:
            The validated instance.

        Raises:
            AllValuesNullError:
                If all multipliers are set to ``None``.
        """
        if any(getattr(self, field) is not None for field in type(self).model_fields):
            return self

        raise AllValuesNullError("pattern_multipliers")

    def get_patterns(self, term: str) -> list[tuple[PatternName, str, int | None]]:
        """Generate SQL pattern variants for a term.

        Produces pattern strings suitable for ``LIKE`` comparisons, paired with their
        associated multipliers.

        Pattern formats:
            - exact: ``term``
            - prefix: ``term%``
            - suffix: ``%term``
            - substring: ``%term%``

        Args:
            term:
                The raw search term.

        Returns:
            A list of tuples containing:
                - Pattern name
                - SQL pattern string
                - Associated multiplier (or ``None`` if disabled)
        """
        return [
            ("exact", term, self.exact),
            ("prefix", f"{term}%", self.prefix),
            ("suffix", f"%{term}", self.suffix),
            ("substring", f"%{term}%", self.substring),
        ]

    def serialize(self) -> bytes:
        """Serialize multipliers into compact binary format.

        Serialization behavior:
            - Uses a presence bitmask to encode non-default values.
            - Uses a separate bitmask to encode explicit ``None`` values.
            - Stores modified multipliers as signed 8-bit integers.
            - Omits fields that match default values.

        Returns:
            A bytes object representing serialized multipliers.
        """
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
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple[PatternMultipliers, int]:
        """Deserialize multipliers from binary format.

        Args:
            data:
                Serialized byte sequence.
            offset:
                Starting offset within the sequence.

        Returns:
            A tuple containing:
                - The reconstructed ``PatternMultipliers`` instance
                - The updated byte offset
        """
        presence, null_presence = struct.unpack_from("!BB", data, offset)
        offset += 2
        values: dict[str, int | None] = {}

        for flag in PatternMultiplierFieldFlag:
            if presence & flag:
                flag_name = str(flag.name)
                values[flag_name] = struct.unpack_from("!b", data, offset)[0]
                offset += 1
            elif null_presence & flag:
                values[str(flag.name)] = None

        return cls(**values), offset


# Default multiplier values used to determine serialization deltas.
_DEFAULTS = PatternMultipliers().model_dump()

_pattern_multiplier_field_flag_map: dict[str, int] = {
    field: auto() for field in PatternMultipliers.model_fields
}
PatternMultiplierFieldFlag = IntFlag(
    "PatternMultiplierFieldFlag", _pattern_multiplier_field_flag_map
)
"""Bitmask flags representing individual pattern multipliers.

Used to encode presence and null-state information during binary serialization.
"""
