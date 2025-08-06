from sqlalchemy.sql.sqltypes import Integer, String
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped

from .base import Base


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
