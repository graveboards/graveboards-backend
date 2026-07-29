from __future__ import annotations

def validate_model_attrs(model_name: str, attrs: dict, valid_attrs: set[str]) -> None:
    """Validate that all attributes in a dict are valid for the given model.

    Args:
        model_name:
            The model class name for error messages.
        attrs:
            Dictionary of attributes to validate.
        valid_attrs:
            Set of valid attribute names (column_names | relationship_names or similar).

    Raises:
        ValueError:
            If any attribute in ``attrs`` is not in ``valid_attrs``.
    """
    for key in attrs:
        if key not in valid_attrs:
            raise ValueError(f"{model_name} has no attribute '{key}'")
