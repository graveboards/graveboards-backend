from connexion.exceptions import Forbidden


class RestrictionViolationError(Exception):
    def __init__(self, restriction_type: str, detail: str):
        self.restriction_type = restriction_type
        self._detail = detail
        super().__init__(detail)

    @property
    def detail(self) -> str:
        return self._detail
