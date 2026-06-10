from typing import Optional
from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from app.database.literals import RoleNameLiteral
from .base_model_extra import BaseModelExtra


class RoleSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: RoleNameLiteral


class RoleCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: RoleNameLiteral


class RoleUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: Optional[RoleNameLiteral] = None
