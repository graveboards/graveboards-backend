from pydantic.main import BaseModel


class PageSchema(BaseModel):
    html: str
    raw: str
