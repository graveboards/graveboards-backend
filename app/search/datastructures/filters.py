import struct
from typing import Iterator, Any, Optional
from collections.abc import ItemsView

from pydantic.main import BaseModel
from pydantic.root_model import RootModel
from pydantic.functional_validators import model_validator
from pydantic_core import ValidationError

from app.database.utils import extract_inner_types, validate_type
from app.exceptions import (
    FieldNotSupportedError,
    TypeValidationError,
    FieldValidationError,
    UnknownFieldCategoryError,
    FieldConditionValidationError
)
from app.search.enums import SearchableFieldCategory, ModelField, ModelFieldId, SearchableFieldCategoryFlag
from .conditions import Conditions, ConditionValue


class FieldFilters(RootModel):
    root: dict[str, Conditions]

    def __iter__(self) -> Iterator[str]:
        return iter(self.root)

    def __getitem__(self, key: str) -> Conditions:
        return self.root[key]

    def __len__(self) -> int:
        return len(self.root)

    def items(self) -> ItemsView[str, Conditions]:
        return self.root.items()

    def validate_against_sqlalchemy_model(self, category: SearchableFieldCategory):
        column_map = category.model_class.value.__annotations__

        for field_name, conditions in self.root.items():
            try:
                model_field = ModelField.from_category_field(category.value, field_name)

                if model_field.is_aliased:
                    column = column_map[model_field.alias]
                else:
                    column = column_map[field_name]
            except (KeyError, ValueError):
                raise FieldNotSupportedError(category.value, field_name)

            expected_type = extract_inner_types(column)

            for value in conditions.values_for_validation():
                if value is not None:
                    try:
                        validate_type(expected_type, value)
                    except TypeValidationError as e:
                        raise FieldValidationError(category.value, field_name, value, *e.target_types) from e

    def serialize(self, category: SearchableFieldCategory) -> bytes:
        length = struct.pack("!B", len(self))
        chunks = []

        for field_name, conditions in self.root.items():
            model_field = ModelField.from_category_field(category.value, field_name)
            model_field_id = ModelFieldId[model_field.name]
            chunks.append(struct.pack("!H", model_field_id))
            chunks.append(conditions.serialize())

        return length + b"".join(chunks)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["FieldFilters", int]:
        length = struct.unpack_from("!B", data, offset=offset)[0]
        offset += 1
        values = {}

        for _ in range(length):
            model_field_id = ModelFieldId(struct.unpack_from("!H", data, offset=offset)[0])
            offset += 2
            model_field = ModelField[model_field_id.name]
            value, offset = Conditions.deserialize(data, offset=offset)
            values[model_field.field_name] = value

        return cls(**values), offset


class FiltersSchema(BaseModel):
    profile: Optional[FieldFilters] = None
    beatmap: Optional[FieldFilters] = None
    beatmapset: Optional[FieldFilters] = None
    request: Optional[FieldFilters] = None

    @model_validator(mode="before")
    @classmethod
    def validate_filters(cls, filters: dict[str, Any]) -> dict[str, Any]:
        validated_filters = {}

        for category_name, field_filters in filters.items():
            try:
                filter_category = SearchableFieldCategory.from_name(category_name)
            except ValueError:
                raise UnknownFieldCategoryError(category_name)

            if field_filters is None:
                continue

            if isinstance(field_filters, FieldFilters):
                field_filters.validate_against_sqlalchemy_model(filter_category)
                validated_filters[category_name] = field_filters
                continue

            if not isinstance(field_filters, dict):
                raise TypeError(f"Category '{category_name}' expected dict, got {type(field_filters).__name__}")

            validated_field_filters = {}

            for field_name, value in field_filters.items():
                try:
                    if isinstance(value, ConditionValue):
                        validated_field_filters[field_name] = value
                    else:
                        validated_field_filters[field_name] = Conditions.model_validate(value)
                except ValidationError as e:
                    for error in e.errors():
                        key_path = " -> ".join(map(str, error.get("loc", [])))
                        loc_detail = f" (at: {key_path})" if key_path else ""

                        if "ctx" in error and "error" in error["ctx"]:
                            msg = error["ctx"]["error"]
                        else:
                            msg = error.get("msg", "Unknown validation error")

                        detail = f"{msg}{loc_detail}"
                        raise FieldConditionValidationError(filter_category.value, field_name, detail=detail) from e

            validated_filters[category_name] = FieldFilters.model_validate(validated_field_filters)
            validated_filters[category_name].validate_against_sqlalchemy_model(filter_category)

        return validated_filters

    def serialize(self) -> bytes:
        presence = 0
        chunks = []

        if self.profile:
            presence |= SearchableFieldCategoryFlag.PROFILE
            chunks.append(self.profile.serialize(SearchableFieldCategory.PROFILE))

        if self.beatmap:
            presence |= SearchableFieldCategoryFlag.BEATMAP
            chunks.append(self.beatmap.serialize(SearchableFieldCategory.BEATMAP))

        if self.beatmapset:
            presence |= SearchableFieldCategoryFlag.BEATMAPSET
            chunks.append(self.beatmapset.serialize(SearchableFieldCategory.BEATMAPSET))

        if self.request:
            presence |= SearchableFieldCategoryFlag.REQUEST
            chunks.append(self.request.serialize(SearchableFieldCategory.REQUEST))

        presence_byte = struct.pack("!B", presence)

        return presence_byte + b"".join(chunks)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["FiltersSchema", int]:
        presence = struct.unpack_from("!B", data, offset=offset)[0]
        offset += 1

        profile = beatmap = beatmapset = request = None

        if presence & SearchableFieldCategoryFlag.PROFILE:
            profile, offset = FieldFilters.deserialize(data, offset=offset)

        if presence & SearchableFieldCategoryFlag.BEATMAP:
            beatmap, offset = FieldFilters.deserialize(data, offset=offset)

        if presence & SearchableFieldCategoryFlag.BEATMAPSET:
            beatmapset, offset = FieldFilters.deserialize(data, offset=offset)

        if presence & SearchableFieldCategoryFlag.REQUEST:
            request, offset = FieldFilters.deserialize(data, offset=offset)

        return cls(
            profile=profile,
            beatmap=beatmap,
            beatmapset=beatmapset,
            request=request
        ), offset
