from typing import Optional, TYPE_CHECKING, ClassVar

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra
from .beatmapset_listing import BeatmapsetListingSchema

if TYPE_CHECKING:
    from .request import RequestSchema
    from .queue_listing import QueueListingSchema


class RequestListingSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    request_id: int
    beatmapset_listing_id: int

    request: "RequestSchema"
    beatmapset_listing: "BeatmapsetListingSchema"
    queue_listing: Optional["QueueListingSchema"] = None

    FRONTEND_INCLUDE: ClassVar = {
        "request": {
            "beatmapset_id": True,
            "user_id": True,
            "status": True,
            "comment": True,
            "user_profile": {"username", "avatar_url"},
            "queue": {"name"}
        },
        "beatmapset_listing": BeatmapsetListingSchema.FRONTEND_INCLUDE
    }
