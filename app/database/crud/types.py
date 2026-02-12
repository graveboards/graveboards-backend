from typing import TypeVar, Mapping, Union, Iterable, Literal

AttrName = TypeVar("AttrName", bound=str)
Sorting = Iterable[dict[Literal["field", "order"], Union[AttrName, Literal["asc", "desc"]]]]
Include = Mapping[AttrName, Union[bool, "Include[AttrName]"]]
