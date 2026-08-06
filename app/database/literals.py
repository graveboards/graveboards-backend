"""Typing literals enumerating role and request-status values."""

from __future__ import annotations

from typing import Literal

__all__ = ["RequestStatusIntLiteral", "RequestStatusLiteral", "RoleNameLiteral"]


RoleNameLiteral = Literal["admin"]
RequestStatusLiteral = Literal["rejected", "pending", "accepted"]
RequestStatusIntLiteral = Literal[-1, 0, 1]
