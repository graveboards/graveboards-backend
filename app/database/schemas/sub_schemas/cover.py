from typing import Optional

from pydantic.main import BaseModel


class CoverSchema(BaseModel):
    custom_url: Optional[str]
    url: Optional[str]
    id: Optional[int]
