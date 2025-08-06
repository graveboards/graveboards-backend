from typing import TypedDict, Literal, Union, NotRequired

LoadingStrategy = Literal["joinedload", "selectinload", "noload"]
LoadingOptionsConfig = Union[bool, LoadingStrategy, "LoadingNode"]
LoadingOptions = dict[str, LoadingOptionsConfig]


class LoadingNode(TypedDict):
    strategy: NotRequired[LoadingStrategy]
    options: "LoadingOptions"
