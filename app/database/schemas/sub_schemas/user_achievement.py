from datetime import datetime

from pydantic.main import BaseModel


class UserAchievementSchema(BaseModel):
    achieved_at: datetime
    achievement_id: int
