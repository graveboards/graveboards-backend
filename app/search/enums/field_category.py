from enum import Enum, IntFlag, auto

from app.database.models import ModelClass


class SearchableFieldCategory(Enum):
    """Logical category of searchable models.

    Maps a public-facing category name (e.g., ``"beatmapset"``) to its corresponding
    internal ``ModelClass``.

    This enum serves as the boundary between external query input and internal model
    resolution, ensuring category names are validated and storage-layer agnostic.
    """
    PROFILE = "profile", ModelClass.PROFILE
    BEATMAP = "beatmap", ModelClass.BEATMAP_SNAPSHOT
    BEATMAPSET = "beatmapset", ModelClass.BEATMAPSET_SNAPSHOT
    QUEUE = "queue", ModelClass.QUEUE
    REQUEST = "request", ModelClass.REQUEST
    # TODO: Add beatmap tags and beatmapset tags

    def __init__(self, name: str, model_class: ModelClass):
        self._value_ = name
        self.model_class = model_class

    @classmethod
    def from_name(cls, name: str) -> "SearchableFieldCategory":
        """Resolve a category from its external string name.

        Args:
            name:
                Public category name.

        Returns:
            Matching ``SearchableFieldCategory``.

        Raises:
            ValueError:
                If no matching category exists.
        """
        for member in cls.__members__.values():
            if name == member.value:
                return member

        raise ValueError(f"No SearchableFieldCategoryFlag exists by the name of '{name}'")

    @classmethod
    def from_model_class(cls, model_class: ModelClass) -> "SearchableFieldCategory":
        """Resolve a category from its internal ``ModelClass``.

        Args:
            model_class:
                Internal model class identifier.

        Returns:
            Matching ``SearchableFieldCategory``.

        Raises:
            ValueError:
                If no matching category exists.
        """
        for member in cls.__members__.values():
            if model_class is member.model_class:
                return member

        raise ValueError(f"No SearchableFieldCategoryFlag exists with model class {model_class}")


SearchableFieldCategoryFlag = IntFlag("SearchableFieldCategoryFlag", {category.name: auto() for category in SearchableFieldCategory})
"""Bitmask representation of searchable field categories.

Used for compact encoding of multiple categories within serialized query payloads.
"""

CATEGORY_NAMES = [category.value for category in SearchableFieldCategory]
"""List of valid external category names."""
