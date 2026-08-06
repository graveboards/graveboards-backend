"""Searchable field category enumerations."""

from __future__ import annotations

from enum import Enum, IntFlag, auto
from typing import Any

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

    def __init__(self, name: str, model_class: ModelClass[Any]):
        """Initialize a searchable field category.

        Args:
            name:
                The external category name.
            model_class:
                The corresponding internal model class.
        """
        self._category_value: str = name
        self.model_class = model_class

    @property
    def category_value(self) -> str:
        """Return the external category name.

        Returns:
            The string name of the category.
        """
        return self._category_value

    @classmethod
    def from_name(cls, name: str) -> SearchableFieldCategory:
        """Resolve a category from its external string name.

        Args:
            name:
                Public category name.

        Returns:
        -------
            Matching ``SearchableFieldCategory``.

        Raises:
        ------
            ValueError:
                If no matching category exists.
        """
        for member in cls.__members__.values():
            if name == member._category_value:
                return member

        raise ValueError(f"No SearchableFieldCategoryFlag exists by the name of '{name}'")

    @classmethod
    def from_model_class(cls, model_class: ModelClass[Any]) -> SearchableFieldCategory:
        """Resolve a category from its internal ``ModelClass``.

        Args:
            model_class:
                Internal model class identifier.

        Returns:
        -------
            Matching ``SearchableFieldCategory``.

        Raises:
        ------
            ValueError:
                If no matching category exists.
        """
        for member in cls.__members__.values():
            if model_class is member.model_class:
                return member

        raise ValueError(f"No SearchableFieldCategoryFlag exists with model class {model_class}")


class SearchableFieldCategoryFlag(IntFlag):
    """Bitmask representation of searchable field categories.

    Used for compact encoding of multiple categories within serialized query payloads.
    """

    PROFILE = auto()
    BEATMAP = auto()
    BEATMAPSET = auto()
    QUEUE = auto()
    REQUEST = auto()


CATEGORY_NAMES: list[str] = [category._category_value for category in SearchableFieldCategory]
"""List of valid external category names."""
