from pydantic.main import BaseModel
from pydantic.config import ConfigDict
from pydantic.fields import Field
from pydantic.functional_serializers import model_serializer
from pydantic_core.core_schema import SerializationInfo


class CoversSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cover: str
    cover_2x: str = Field(alias="cover@2x")
    card: str
    card_2x: str = Field(alias="card@2x")
    list: str
    list_2x: str = Field(alias="list@2x")
    slimcover: str
    slimcover_2x: str = Field(alias="slimcover@2x")

    @model_serializer
    def serialize_with_aliases(self, info: SerializationInfo):
        included = info.include

        return {
            self.model_fields[field].alias or field: value
            for field, value in self.__dict__.items()
            if included is None or field in included
        }
