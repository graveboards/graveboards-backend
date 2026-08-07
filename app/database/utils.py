"""Utilities for type introspection and SQL filter construction."""

from __future__ import annotations

import sys
import types
from typing import TYPE_CHECKING, Any, get_args, get_origin
from typing import cast as typing_cast

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import all_, any_, cast
from sqlalchemy.sql.elements import (
    BinaryExpression,
    BindParameter,
    CollectionAggregate,
    ColumnClause,
    ColumnElement,
    literal,
)
from sqlalchemy.sql.functions import func

from app.database.enums import FilterOperator
from app.exceptions import TypeValidationError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.sql.selectable import ScalarSelect

    from app.database.ctes.hashable_cte import HashableCTE

__all__ = ["extract_inner_types", "get_filter_condition", "resolve_annotation", "validate_type"]


def extract_inner_types(annotated_type: Any) -> type | tuple[type, ...]:
    """Extract concrete inner types from nested typing annotations.

    Unwraps Optional, Union, and generic containers to determine the underlying runtime
    type(s).

    Args:
        annotated_type:
            A typing-annotated type.

    Returns:
    -------
        A single type or tuple of possible types.
    """
    current = annotated_type

    while get_origin(current):
        origin = get_origin(current)
        args = get_args(current)

        if origin is types.UnionType:
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1 or len(non_none_args) == 2:
                return typing_cast("type", non_none_args[0])
            return tuple(non_none_args)
        current = args[0] if args else current

    return typing_cast("type", current)


def resolve_annotation(model: type, name: str) -> Any:
    """Resolve a (possibly lazy) annotation for a model attribute to its runtime type.

    ``from __future__ import annotations`` stores annotations as strings; this evaluates
    them in the model's module namespace so callers can deal with concrete types.

    Args:
        model:
            The model class owning the attribute.
        name:
            Attribute name.

    Returns:
    -------
        The resolved runtime type (or the raw annotation if it cannot be resolved).
    """
    annotation = model.__annotations__.get(name)
    if not isinstance(annotation, str):
        return annotation

    module = sys.modules.get(model.__module__)
    if module is None:
        return annotation

    try:
        return eval(annotation, vars(module))
    except NameError, SyntaxError:
        return annotation


def validate_type(expected_type: Any, value: Any) -> None:
    """Recursively validate a value against a typing annotation.

    Supports:
        - Union / Optional
        - list / tuple
        - dict
        - Numeric widening (int accepted for float)

    Args:
        expected_type:
            Typing annotation to validate against.
        value:
            Runtime value to validate.

    Raises:
    ------
        TypeValidationError:
            If validation fails at any level.
    """
    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin is types.UnionType:
        for arg in args:
            try:
                validate_type(arg, value)
                return
            except TypeValidationError:
                continue

        raise TypeValidationError(type(value), *args)

    if origin in (list, tuple):
        if not isinstance(value, origin):
            raise TypeValidationError(type(value), origin)

        iterable_value = typing_cast("Iterable[Any]", value)
        item_types = args if origin is tuple and len(args) > 1 else [args[0]]

        for i, item in enumerate(iterable_value):
            expected_item_type = item_types[min(i, len(item_types) - 1)]
            validate_type(expected_item_type, item)

        return

    if origin is dict:
        if not isinstance(value, dict):
            raise TypeValidationError(type(value), dict)

        key_type, val_type = args

        for k, v in value.items():
            validate_type(key_type, k)
            validate_type(val_type, v)

        return

    if expected_type is float:
        if not isinstance(value, (float, int)):
            raise TypeValidationError(type(value), float, int)

        return

    if not isinstance(value, expected_type):
        raise TypeValidationError(type(value), expected_type)


def get_filter_condition(
    filter_operator: FilterOperator,
    target: InstrumentedAttribute[Any]
    | ColumnClause[Any]
    | HashableCTE
    | ScalarSelect[Any]
    | ColumnElement[Any],
    value: Any,
    is_aggregated: bool = False,
) -> BinaryExpression[Any] | BindParameter[Any] | CollectionAggregate[Any] | ColumnElement[bool]:
    """Construct a SQLAlchemy filter condition dynamically.

    For non-aggregated columns, delegates directly to the operator's bound method.

    For aggregated queries, constructs array-based comparisons using PostgreSQL
    aggregation functions to support filtering across grouped results.

    Args:
        filter_operator:
            Logical operator abstraction.
        target:
            Column or instrumented attribute being filtered.
        value:
            Comparison value.
        is_aggregated:
            Whether the filter applies to grouped results.

    Returns:
    -------
        SQLAlchemy boolean expression suitable for WHERE or HAVING.

    Raises:
    ------
        ValueError:
            If an unsupported filter operator is provided.
    """
    if not is_aggregated:
        if not isinstance(filter_operator, FilterOperator):
            raise ValueError(f"Invalid filter operator: {filter_operator}")
        return filter_operator.method(target, value)  # type: ignore[no-any-return]

    array_agg = func.array_agg(target)

    if not isinstance(target, (InstrumentedAttribute, ColumnClause)):
        raise ValueError(
            f"Aggregated filter operators require a column target, got {type(target).__name__}"
        )

    match filter_operator:
        case FilterOperator.EQ:
            return literal(value) == any_(array_agg)
        case FilterOperator.NEQ:
            return literal(value) != all_(array_agg)
        case FilterOperator.GT:
            return any_(array_agg) > literal(value)
        case FilterOperator.LT:
            return any_(array_agg) < literal(value)
        case FilterOperator.GTE:
            return any_(array_agg) >= literal(value)
        case FilterOperator.LTE:
            return any_(array_agg) <= literal(value)
        case FilterOperator.IN:
            return array_agg.op("&&")(cast(literal(value), ARRAY(target.type)))
        case FilterOperator.NOT_IN:
            return ~array_agg.op("&&")(cast(literal(value), ARRAY(target.type)))
        case FilterOperator.IS_NULL:
            return func.bool_and(target.is_(None))
        case FilterOperator.REGEX:
            return func.bool_or(target.op("~")(literal(value)))
        case FilterOperator.NOT_REGEX:
            return func.bool_and(~target.op("~")(literal(value)))
        case _:
            raise ValueError(f"Invalid filter operator: {filter_operator}")
