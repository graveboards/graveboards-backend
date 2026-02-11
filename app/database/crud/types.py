from typing import TypeVar, Mapping, Union

AttrName = TypeVar("AttrName", bound=str)
Include = Mapping[AttrName, Union[bool, "Include[AttrName]"]]
