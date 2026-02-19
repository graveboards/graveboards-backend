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
    """Field-level filtering conditions for a single category.

    Wraps a mapping of field names to ``Conditions`` objects and provides SQLAlchemy
    model validation and compact binary serialization support.
    """
    root: dict[str, Conditions]

    def __iter__(self) -> Iterator[str]:
        """Iterate over filter field names.

        Returns:
            An iterator over field names.
        """
        return iter(self.root)

    def __getitem__(self, key: str) -> Conditions:
        """Retrieve conditions for a specific field.

        Args:
            key:
                Field name.

        Returns:
            The corresponding ``Conditions`` instance.

        Raises:
            KeyError:
                If the field does not exist.
        """
        return self.root[key]

    def __len__(self) -> int:
        """Return the number of filtered fields.

        Returns:
            The number of field filters.
        """
        return len(self.root)

    def items(self) -> ItemsView[str, Conditions]:
        """Return a view of field-condition pairs.

        Returns:
            An items view of field names and their associated conditions.
        """
        return self.root.items()

    def validate_against_sqlalchemy_model(self, category: SearchableFieldCategory):
        """Validate filter fields and values against the SQLAlchemy model.

        Ensures:
            - Each field exists on the underlying model
            - Aliased fields resolve correctly
            - All condition values conform to the column's expected type

        Args:
            category:
                Field category defining the SQLAlchemy model.

        Raises:
            FieldNotSupportedError:
                If a field is not supported for the category.
            FieldValidationError:
                If a condition value does not match the expected type.
        """
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
        """Serialize field filters into compact binary format.

        Serialization behavior:
            - Encodes the number of filtered fields as a single byte.
            - Stores each field using its ``ModelFieldId``.
            - Appends serialized ``Conditions`` for each field.

        Args:
            category:
                Category used to resolve model field identifiers.

        Returns:
            A bytes object representing serialized field filters.
        """
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
        """Deserialize field filters from binary format.

        Args:
            data:
                Serialized byte sequence.
            offset:
                Starting offset within the sequence.

        Returns:
            A tuple containing:
                - The reconstructed ``FieldFilters`` instance
                - The updated byte offset
        """
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
    """Structured filtering configuration across categories.

    Validates filter fields against SQLAlchemy models and supports compact binary
    serialization.
    """
    profile: Optional[FieldFilters] = None
    beatmap: Optional[FieldFilters] = None
    beatmapset: Optional[FieldFilters] = None
    queue: Optional[FieldFilters] = None
    request: Optional[FieldFilters] = None

    @model_validator(mode="before")
    @classmethod
    def validate_filters(cls, filters: dict[str, Any]) -> dict[str, Any]:
        """Validate category-level and field-level filter definitions.

        Validation steps:
            - Ensures category names are recognized
            - Validates each field's ``Conditions`` definition
            - Performs SQLAlchemy model compatibility checks
            - Converts raw dictionaries into ``FieldFilters`` instances

        Args:
            filters:
                Raw filter input mapping category names to definitions.

        Returns:
            A validated mapping of category names to ``FieldFilters`` instances.

        Raises:
            UnknownFieldCategoryError:
                If a category name is invalid.
            TypeError:
                If a category definition is not a dictionary.
            FieldConditionValidationError:
                If a field condition is invalid.
            FieldNotSupportedError:
                If a field is not supported by the model.
            FieldValidationError:
                If a value fails type validation.
        """
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
        """Serialize enabled category filters into compact binary format.

        Serialization behavior:
            - Encodes category presence using a bitmask.
            - Serializes each enabled category in deterministic order.
            - Appends serialized ``FieldFilters`` per category.

        Returns:
            A bytes object representing the serialized filtering configuration.
        """
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

        if self.queue:
            presence |= SearchableFieldCategoryFlag.QUEUE
            chunks.append(self.queue.serialize(SearchableFieldCategory.QUEUE))

        if self.request:
            presence |= SearchableFieldCategoryFlag.REQUEST
            chunks.append(self.request.serialize(SearchableFieldCategory.REQUEST))

        presence_byte = struct.pack("!B", presence)

        return presence_byte + b"".join(chunks)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["FiltersSchema", int]:
        """Deserialize filtering configuration from binary format.

        Args:
            data:
                Serialized byte sequence.
            offset:
                Starting offset within the sequence.

        Returns:
            A tuple containing:
                - The reconstructed ``FiltersSchema`` instance
                - The updated byte offset
        """
        presence = struct.unpack_from("!B", data, offset=offset)[0]
        offset += 1

        profile = beatmap = beatmapset = queue = request = None

        if presence & SearchableFieldCategoryFlag.PROFILE:
            profile, offset = FieldFilters.deserialize(data, offset=offset)

        if presence & SearchableFieldCategoryFlag.BEATMAP:
            beatmap, offset = FieldFilters.deserialize(data, offset=offset)

        if presence & SearchableFieldCategoryFlag.BEATMAPSET:
            beatmapset, offset = FieldFilters.deserialize(data, offset=offset)

        if presence & SearchableFieldCategoryFlag.QUEUE:
            queue, offset = FieldFilters.deserialize(data, offset=offset)

        if presence & SearchableFieldCategoryFlag.REQUEST:
            request, offset = FieldFilters.deserialize(data, offset=offset)

        return cls(
            profile=profile,
            beatmap=beatmap,
            beatmapset=beatmapset,
            queue=queue,
            request=request
        ), offset
