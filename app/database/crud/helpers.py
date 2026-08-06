"""Shared CRUD helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

__all__ = ["validate_model_attrs"]


def validate_model_attrs(
    model_name: str, attrs: Mapping[str, Any], valid_attrs: Iterable[str]
) -> None:
    """Raise if any key in ``attrs`` is not a valid attribute of the model.

    Args:
        model_name:
            Name of the model, used for the error message.
        attrs:
            Mapping of supplied field names to values.
        valid_attrs:
            Names accepted by the model (columns and relationships).

    Raises:
    ------
        ValueError:
            If a supplied key is not in ``valid_attrs``.
    """
    valid = set(valid_attrs)

    for key in attrs:
        if key not in valid:
            raise ValueError(f"{model_name} has no attribute '{key}'")
