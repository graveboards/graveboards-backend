import shlex
import struct
from typing import Iterator, Union, Annotated

from pydantic.main import BaseModel
from pydantic.fields import Field
from pydantic.functional_validators import field_validator

from app.search.enums import Scope
from .field_weights import FieldWeights
from .pattern_multipliers import PatternMultipliers


class SearchTermsSchema(BaseModel):
    terms: list[Annotated[str, Field(max_length=255)]]
    case_sensitive: bool = False
    pattern_multipliers: PatternMultipliers = PatternMultipliers()
    field_weights: FieldWeights = FieldWeights()

    def __iter__(self) -> Iterator[str]:
        return iter(self.terms)

    @field_validator("terms", mode="before")
    @classmethod
    def validate_terms(cls, raw_terms: Union[str, list[str]]) -> list[str]:
        if isinstance(raw_terms, str):
            try:
                parsed = shlex.split(raw_terms)
            except ValueError as e:
                raise ValueError(f"Invalid search string: {e}")
        elif isinstance(raw_terms, list):
            if not all(isinstance(item, str) for item in raw_terms):
                raise TypeError("All search terms must be strings")
            parsed = raw_terms
        else:
            raise TypeError("terms must be a string or list of strings")

        if not (terms := [term for term in parsed if term.strip() != ""]):
            raise ValueError("Search terms must not only contain empty strings")

        return terms

    def validate_against_scope(self, scope: Scope):
        self.field_weights.validate_against_scope(scope)

    def serialize(self, scope: Scope) -> bytes:
        encoded_terms = [t.encode() for t in self.terms]
        term_count = struct.pack("!B", len(encoded_terms))
        term_data = b"".join(struct.pack("!B", len(t)) + t for t in encoded_terms)

        flags = 1 if self.case_sensitive else 0
        flag_byte = struct.pack("!B", flags)

        return (
            term_count +
            term_data +
            flag_byte +
            self.pattern_multipliers.serialize() +
            self.field_weights.serialize(scope)
        )

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["SearchTermsSchema", int]:
        term_count = struct.unpack_from("!B", data, offset=offset)[0]
        offset += 1
        terms = []

        for _ in range(term_count):
            length = struct.unpack_from("!B", data, offset=offset)[0]
            offset += 1
            term = data[offset:offset + length].decode()
            offset += length
            terms.append(term)

        flags = struct.unpack_from("!B", data, offset=offset)[0]
        offset += 1
        case_sensitive = bool(flags & 1)

        pattern_multipliers, offset = PatternMultipliers.deserialize(data, offset=offset)
        field_weights, offset = FieldWeights.deserialize(data, offset=offset)

        return cls(
            terms=terms,
            case_sensitive=case_sensitive,
            pattern_multipliers=pattern_multipliers,
            field_weights=field_weights
        ), offset
