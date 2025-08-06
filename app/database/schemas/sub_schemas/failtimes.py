from typing import Optional

from pydantic.main import BaseModel


class FailtimesSchema(BaseModel):
    exit: Optional[list[int]]
    fail: Optional[list[int]]
