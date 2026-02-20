from typing import Mapping, Union, Iterable, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from app.search.datastructures import ConditionField, ConditionValue

type AttrName = str
"""Type alias representing a model attribute name."""

type RelName = str
"""Type alias representing a model relationship name."""

type AttrPath = str
"""Type alias representing a model attribute path."""

type Sorting = Iterable[dict[Literal["field", "order"], Union[AttrPath, Literal["asc", "desc"]]]]
"""Type alias describing sorting configuration for read operations.

Expected format:
    Iterable of dictionaries with:
        {
            "field": "Model.attribute",
            "order": "asc" | "desc"
        }

Used by the read layer to construct validated ORDER BY clauses.
"""

type Conditions = Mapping[ConditionField, ConditionValue | None]

type Filters = Mapping[Union[AttrName, RelName], Union[ConditionValue, None, Conditions, "Filters[RelName]"]]
"""Type alias describing nested filtering configurations for read operations.

Expected format:
    Dictionary of:
        {
            "field": {"eq": "value", ...},
            "relationship": Filters,
            ...
        }

Used by the read layer to construct validated WHERE clauses.
"""

type Include = Mapping[AttrName, Union[bool, "Include[AttrName]"]]
"""Type alias describing nested relationship loading configuration.

Maps relationship attribute names to:
    - True: eagerly load the relationship
    - False: explicitly suppress loading
    - dict: recursively configure nested includes

Used to declaratively control eager-loading behavior in read operations.
"""
