from pydantic.main import BaseModel


class RequiredMetaSchema(BaseModel):
    main_ruleset: int
    non_main_ruleset: int
