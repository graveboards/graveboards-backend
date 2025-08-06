from typing import Optional, TYPE_CHECKING

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .queue import QueueSchema
    from .request_listing import RequestListingSchema


class QueueListingSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    queue_id: int

    queue: "QueueSchema"
    request_listings: list["RequestListingSchema"]
