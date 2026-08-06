"""Redis model for osu! client OAuth token storage."""

from __future__ import annotations

from typing import Any

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
        -------
            A dictionary with stringified values.
        """
        serialized_dict = {}

        for key, value in self.__dict__.items():
            serialized_dict[key] = str(value)

        return serialized_dict

    @classmethod
    def deserialize(cls, serialized_dict: dict[str | bytes, str | bytes]) -> OsuClientOAuthToken:
        """Deserialize a stored OAuth token dictionary.

        Args:
            serialized_dict:
                Serialized token data from Redis (keys and values may be bytes or str).

        Returns:
        -------
            A validated ``OsuClientOAuthToken`` instance.
        """
        string_dict = {str(k): str(v) for k, v in serialized_dict.items()}
        deserialized_dict: dict[str, Any] = {}

        for key, value in string_dict.items():
            match key:
                case "expires_in" | "expires_at":
                    deserialized_dict[key] = int(value)
                case _:
                    deserialized_dict[key] = value

        return cls.model_validate(deserialized_dict)
