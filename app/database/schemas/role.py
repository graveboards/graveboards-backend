from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra


class RoleSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
