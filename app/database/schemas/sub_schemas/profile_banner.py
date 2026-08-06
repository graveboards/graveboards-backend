"""Pydantic schema for a profile tournament banner."""

from __future__ import annotations

from pydantic.fields import Field
from pydantic.functional_serializers import model_serializer
from pydantic.main import BaseModel


class ProfileBannerSchema(BaseModel):
    """Banner image URL and tournament for a user's profile."""

    id: int
    tournament_id: int
    image: str | None
    image_2x: str | None = Field(alias="image@2x")

    @model_serializer
    def serialize_with_aliases(self) -> dict[str, str | int | None]:
        """Serialize fields under their field aliases instead of their names."""
        return {
            self.model_fields[field].alias or field: value for field, value in self.__dict__.items()
        }
