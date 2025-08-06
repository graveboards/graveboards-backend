from typing import Optional

from pydantic.main import BaseModel


class AvailabilitySchema(BaseModel):
    download_disabled: bool
    more_information: Optional[str]
