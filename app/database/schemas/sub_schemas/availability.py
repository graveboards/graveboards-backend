from __future__ import annotations
from pydantic.main import BaseModel


class AvailabilitySchema(BaseModel):
    download_disabled: bool
    more_information: str | None
