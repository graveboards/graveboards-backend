from typing import Optional

from pydantic.main import BaseModel
from pydantic.fields import Field
from pydantic.functional_serializers import model_serializer


class ProfileBannerSchema(BaseModel):
    id: int
    tournament_id: int
    image: Optional[str]
    image_2x: Optional[str] = Field(alias="image@2x")

    @model_serializer
    def serialize_with_aliases(self):
        return {self.model_fields[field].alias or field: value for field, value in self.__dict__.items()}
