from typing import Mapping, Union, Iterable, Literal

type AttrName = str
"""Type alias representing a model attribute name."""

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

type Include = Mapping[AttrName, Union[bool, "Include[AttrName]"]]
"""Type alias describing nested relationship loading configuration.

Maps relationship attribute names to:
    - True: eagerly load the relationship
    - False: explicitly suppress loading
    - dict: recursively configure nested includes

Used to declaratively control eager-loading behavior in read operations.
"""
