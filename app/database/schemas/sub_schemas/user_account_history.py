from datetime import datetime
from typing import Literal

from pydantic.main import BaseModel


class UserAccountHistorySchema(BaseModel):
    id: int
    timestamp: datetime
    length: int
    permanent: bool
    type: Literal["note", "restriction", "silence", "tournament_ban"]
    description: str | None
