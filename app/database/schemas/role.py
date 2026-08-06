"""Pydantic schemas for roles."""

from __future__ import annotations

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from app.database.literals import RoleNameLiteral

from .base_model_extra import BaseModelExtra


class RoleSchema(BaseModel, BaseModelExtra):
    """Role record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: RoleNameLiteral


class RoleCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a role."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: RoleNameLiteral


class RoleUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing role."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: RoleNameLiteral | None = None
