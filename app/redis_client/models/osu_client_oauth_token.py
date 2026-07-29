from __future__ import annotations
from typing import Any
from typing import cast as typing_cast

from pydantic.main import BaseModel


class OsuClientOAuthToken(BaseModel):
    """Represents an osu! OAuth client credentials token."""

    access_token: str
    token_type: str
    expires_in: int
    expires_at: int

    def serialize(self) -> dict[str, str]:
        """Serialize the token for Redis storage.

        Returns:
            A dictionary with stringified values.
        """
        serialized_dict = {}

        for key, value in self.__dict__.items():
            serialized_dict[key] = str(value)

        return serialized_dict

    @classmethod
    def deserialize(cls, serialized_dict: dict[str, str]) -> OsuClientOAuthToken:
        """Deserialize a stored OAuth token dictionary.

        Args:
            serialized_dict:
                Serialized token data.

        Returns:
            A validated ``OsuClientOAuthToken`` instance.
        """
        deserialized_dict: dict[str, Any] = {}

        for key, value in serialized_dict.items():
            match key:
                case "expires_in" | "expires_at":
                    deserialized_dict[key] = int(value)
                case _:
                    deserialized_dict[key] = value

        return typing_cast(OsuClientOAuthToken, cls.model_validate(deserialized_dict))
