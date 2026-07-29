from __future__ import annotations
from datetime import datetime

from pydantic.fields import Field
from pydantic.functional_serializers import model_serializer
from pydantic.main import BaseModel


class UserBadgeSchema(BaseModel):
    awarded_at: datetime
    description: str
    image_2x_url: str | None = Field(alias="image@2x_url")
    image_url: str
    url: str

    @model_serializer
    def serialize_with_aliases(self) -> dict[str, str | datetime | None]:
        return {
            self.model_fields[field].alias or field: value for field, value in self.__dict__.items()
        }
