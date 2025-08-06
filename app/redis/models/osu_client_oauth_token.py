from pydantic.main import BaseModel


class OsuClientOAuthToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: int

    def serialize(self) -> dict[str, str]:
        serialized_dict = {}

        for key, value in self.__dict__.items():
            serialized_dict[key] = str(value)

        return serialized_dict

    @classmethod
    def deserialize(cls, serialized_dict: dict[str, str]) -> "OsuClientOAuthToken":
        deserialized_dict = {}

        for key, value in serialized_dict.items():
            match key:
                case "expires_in" | "expires_at":
                    value = int(value)

            deserialized_dict[key] = value

        return cls.model_validate(deserialized_dict)
