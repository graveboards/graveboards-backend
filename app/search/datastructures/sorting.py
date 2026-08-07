"""Sorting data structures for search queries."""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from pydantic import BaseModel, RootModel
from pydantic.functional_serializers import field_serializer

from app.search.enums import ModelField, ModelFieldId, SortingOrder, SortingOrderId

if TYPE_CHECKING:
    from collections.abc import Iterator


class SortingOption(BaseModel):
    """Represents a single field-based sorting rule.

    Defines a sortable model field and its associated ordering direction. Supports
    compact binary serialization.
    """

    field: ModelField
    order: SortingOrder | None = SortingOrder.ASCENDING

    @field_serializer("field", return_type=str)
    def serialize_field(self, field: ModelField) -> str:
        """Serialize the model field to its string representation.

        Args:
            field:
                The ``ModelField`` instance.

        Returns:
        -------
            The string value of the field.
        """
        return str(field.value)

    @field_serializer("order", return_type=str)
    def serialize_order(self, order: SortingOrder) -> str:
        """Serialize the sorting order to its string representation.

        Args:
            order:
                The ``SortingOrder`` enum value.

        Returns:
        -------
            The string value of the sorting order.
        """
        return order.value

    def serialize(self) -> bytes:
        """Serialize the sorting option into compact binary format.

        Serialization behavior:
            - Encodes the field using its ``ModelFieldId``.
            - Encodes the order using ``SortingOrderId``.
            - Stores both as unsigned 8-bit integers.

        Returns:
        -------
            A bytes object representing the serialized sorting option.
        """
        field_id = ModelFieldId[self.field.name]
        if self.order is None:
            raise ValueError("sorting option has no order")
        order_id = SortingOrderId[self.order.name]
        return struct.pack("!BB", field_id, order_id)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple[SortingOption, int]:
        """Deserialize a sorting option from binary format.

        Args:
            data:
                Serialized byte sequence.
            offset:
                Starting offset within the sequence.

        Returns:
        -------
            A tuple containing:
                - The reconstructed ``SortingOption`` instance
                - The updated byte offset
        """
        field_id, order_id = struct.unpack_from("!BB", data, offset=offset)
        offset += 2
        field = ModelField[ModelFieldId(field_id).name]
        order = SortingOrder[SortingOrderId(order_id).name]
        return cls(field=field, order=order), offset


class SortingSchema(RootModel[list[SortingOption]]):
    """Ordered collection of sorting options.

    Preserves priority order of field-based sorting rules and supports compact binary
    serialization.
    """

    root: list[SortingOption]

    def __len__(self) -> int:
        """Return the number of sorting options.

        Returns:
        -------
            The number of configured sorting rules.
        """
        return len(self.root)

    def __iter__(self) -> Iterator[SortingOption]:  # type: ignore[override]
        """Iterate over the sorting options in priority order.

        Returns:
        -------
            An iterator over the configured ``SortingOption`` instances.
        """
        return iter(self.root)

    def serialize(self) -> bytes:
        """Serialize all sorting options into binary format.

        Serialization behavior:
            - Encodes the number of sorting options as a single byte.
            - Serializes each ``SortingOption`` in order of priority.

        Returns:
        -------
            A bytes object representing the serialized sorting schema.
        """
        option_count = struct.pack("!B", len(self))
        chunks = []

        chunks = [option.serialize() for option in self.root]

        return option_count + b"".join(chunks)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple[SortingSchema, int]:
        """Deserialize sorting options from binary format.

        Args:
            data:
                Serialized byte sequence.
            offset:
                Starting offset within the sequence.

        Returns:
        -------
            A tuple containing:
                - The reconstructed ``SortingSchema`` instance
                - The updated byte offset
        """
        option_count = struct.unpack_from("!B", data, offset=offset)[0]
        offset += 1
        options = []

        for _ in range(option_count):
            option, offset = SortingOption.deserialize(data, offset=offset)
            options.append(option)

        return cls.model_validate(options), offset
