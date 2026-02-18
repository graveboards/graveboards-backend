import struct
from typing import Optional, cast
from enum import IntFlag, auto, IntEnum

from pydantic.main import BaseModel
from pydantic.functional_validators import model_validator
from pydantic.config import ConfigDict

from app.search.enums import ScopeLiteral, Scope
from .search_terms import SearchTermsSchema
from .sorting import SortingSchema
from .filters import FiltersSchema


class ScopeId(IntEnum):
    """Byte-level identifier for search scopes.

    Used during binary serialization to represent a ``Scope`` as a compact unsigned
    integer.
    """
    BEATMAPS = auto()
    BEATMAPSETS = auto()
    # SCORES = auto()
    REQUESTS = auto()
    QUEUES = auto()

    @property
    def scope_name(self) -> ScopeLiteral:
        """Return the lowercase string representation of the scope."""
        return cast(ScopeLiteral, self.name.lower())

    @classmethod
    def from_name(cls, name: str) -> "ScopeId":
        """Resolve a scope identifier from its name.

            Args:
                name:
                    Case-insensitive scope name.

            Returns:
                Corresponding ``ScopeId``.

            Raises:
                ValueError:
                    If no matching scope exists.
            """

        for member_name, member in cls.__members__.items():
            if name.upper() == member_name:
                return member

        raise ValueError(f"No ScopeId exists by the name of '{name}'")


class SearchFieldFlag(IntFlag):
    """Bitmask flags indicating which search components are present.

    Used in binary serialization to encode optional sections.
    """
    SEARCH_TERMS = auto()
    SORTING = auto()
    FILTERS = auto()


class SearchSchema(BaseModel):
    """Top-level structured search definition.

    Encapsulates scope, search terms, sorting rules, and filters. Provides compact
    binary serialization for transport or storage.
    """
    model_config = ConfigDict(extra="forbid")

    scope: Scope
    search_terms: Optional[SearchTermsSchema] = None
    sorting: Optional[SortingSchema] = None
    filters: Optional[FiltersSchema] = None

    @model_validator(mode="after")
    def validate_search(self):
        """Validate search terms against the selected scope."""
        if self.search_terms:
            self.search_terms.validate_against_scope(self.scope)

        return self

    def serialize(self) -> bytes:
        """Serialize the search schema into a compact binary format.

        Returns:
            Bytes representing the encoded search configuration.
        """
        scope_byte = struct.pack("!B", ScopeId.from_name(self.scope.name))
        presence = 0
        chunks = []

        if self.search_terms:
            presence |= SearchFieldFlag.SEARCH_TERMS
            chunks.append(SearchTermsSchema.serialize(self.search_terms, self.scope))

        if self.sorting:
            presence |= SearchFieldFlag.SORTING
            chunks.append(SortingSchema.serialize(self.sorting))

        if self.filters:
            presence |= SearchFieldFlag.FILTERS
            chunks.append(FiltersSchema.serialize(self.filters))

        presence_byte = struct.pack("!B", presence)

        return scope_byte + presence_byte + b"".join(chunks)

    @classmethod
    def deserialize(cls, data: bytes) -> "SearchSchema":
        """Deserialize binary data into a ``SearchSchema``.

        Args:
            data:
                Serialized search schema bytes.

        Returns:
            Reconstructed ``SearchSchema``.
        """
        scope_byte, presence = struct.unpack_from("!BB", data)
        offset = 2
        scope = Scope.from_name(ScopeId(scope_byte).scope_name)

        search_terms = sorting = filters = None

        if presence & SearchFieldFlag.SEARCH_TERMS:
            search_terms, offset = SearchTermsSchema.deserialize(data, offset=offset)

        if presence & SearchFieldFlag.SORTING:
            sorting, offset = SortingSchema.deserialize(data, offset=offset)

        if presence & SearchFieldFlag.FILTERS:
            filters, offset = FiltersSchema.deserialize(data, offset=offset)

        return cls(
            scope=scope,
            search_terms=search_terms,
            sorting=sorting,
            filters=filters
        )
