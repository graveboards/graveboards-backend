from pydantic.fields import Field
from pydantic.functional_serializers import model_serializer
from pydantic.main import BaseModel


class ProfileBannerSchema(BaseModel):
    id: int
    tournament_id: int
    image: str | None
    image_2x: str | None = Field(alias="image@2x")

    @model_serializer
    def serialize_with_aliases(self) -> dict[str, str | int | None]:
        return {
            self.model_fields[field].alias or field: value for field, value in self.__dict__.items()
        }
