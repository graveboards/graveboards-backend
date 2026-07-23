from pydantic.main import BaseModel


class FailtimesSchema(BaseModel):
    exit: list[int] | None
    fail: list[int] | None
