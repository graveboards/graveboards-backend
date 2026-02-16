from typing import Literal

__all__ = [
    "RoleNameLiteral",
    "RequestStatusLiteral",
    "RequestStatusIntLiteral"
]


RoleNameLiteral = Literal["admin"]
RequestStatusLiteral = Literal["rejected", "pending", "accepted"]
RequestStatusIntLiteral = Literal[-1, 0, 1]
