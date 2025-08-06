import struct
from typing import Optional, Iterator

from pydantic import BaseModel, RootModel
from pydantic.functional_serializers import field_serializer

from app.search.enums import ModelField, SortingOrder, ModelFieldId, SortingOrderId


class SortingOption(BaseModel):
    field: ModelField
    order: Optional[SortingOrder] = SortingOrder.ASCENDING

    @field_serializer("field", return_type=str)
    def serialize_field(self, field: ModelField) -> str:
        return field.value

    @field_serializer("order", return_type=str)
    def serialize_order(self, order: SortingOrder) -> str:
        return order.value

    def serialize(self) -> bytes:
        field_id = ModelFieldId[self.field.name]
        order_id = SortingOrderId[self.order.name]
        return struct.pack("!BB", field_id, order_id)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["SortingOption", int]:
        field_id, order_id = struct.unpack_from("!BB", data, offset=offset)
        offset += 2
        field = ModelField[ModelFieldId(field_id).name]
        order = SortingOrder[SortingOrderId(order_id).name]
        return cls(field=field, order=order), offset


class SortingSchema(RootModel):
    root: list[SortingOption]

    def __iter__(self) -> Iterator[SortingOption]:
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def serialize(self) -> bytes:
        option_count = struct.pack("!B", len(self))
        chunks = []

        for option in self:
            chunks.append(option.serialize())

        return option_count + b"".join(chunks)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["SortingSchema", int]:
        option_count = struct.unpack_from("!B", data, offset=offset)[0]
        offset += 1
        options = []

        for _ in range(option_count):
            option, offset = SortingOption.deserialize(data, offset=offset)
            options.append(option)

        return cls.model_validate(options), offset
