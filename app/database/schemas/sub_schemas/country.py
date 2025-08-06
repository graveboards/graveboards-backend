from pydantic.main import BaseModel


class CountrySchema(BaseModel):
    code: str
    name: str
