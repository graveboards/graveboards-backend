from sqlalchemy.sql.sqltypes import Integer, String
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped

from .base import Base


class BeatmapsetTag(Base):
    __tablename__ = "beatmapset_tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
