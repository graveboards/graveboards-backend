from typing import TYPE_CHECKING

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped

from .base import Base

if TYPE_CHECKING:
    from .queue import Queue
    from .request_listing import RequestListing


class QueueListing(Base):
    __tablename__ = "queue_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    queue_id: Mapped[int] = mapped_column(Integer, ForeignKey("queues.id"), nullable=False, unique=True)

    # Relationships
    queue: Mapped["Queue"] = relationship(
        "Queue",
        uselist=False
    )
    request_listings: Mapped[list["RequestListing"]] = relationship(
        "RequestListing",
        back_populates="queue_listing"
    )
