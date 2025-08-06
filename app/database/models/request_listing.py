from typing import TYPE_CHECKING

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped

from .base import Base

if TYPE_CHECKING:
    from .request import Request
    from .beatmapset_listing import BeatmapsetListing
    from .queue_listing import QueueListing


class RequestListing(Base):
    __tablename__ = "request_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("requests.id"), nullable=False, unique=True)
    beatmapset_listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmapset_listings.id"), nullable=False, unique=True)
    queue_listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("queue_listings.id"), nullable=False)

    # Relationships
    request: Mapped["Request"] = relationship(
        "Request",
        uselist=False
    )
    beatmapset_listing: Mapped["BeatmapsetListing"] = relationship(
        "BeatmapsetListing",
        uselist=False
    )
    queue_listing: Mapped["QueueListing"] = relationship(
        "QueueListing",
        back_populates="request_listings"
    )
