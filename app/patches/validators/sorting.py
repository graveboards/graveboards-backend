from app.exceptions import ArrayValidationError


def validate_sorting(
    sorting: list,
    schema: dict
):
    """Validate structured sorting directives.

    Ensures each sorting entry:
        - Contains a valid `field`
        - Uses an allowed `order` (default: ``asc``/``desc``)
        - Does not include unexpected keys

    Args:
        sorting:
            List of sorting dictionaries.
        schema:
            OpenAPI schema defining allowed fields and orders.

    Raises:
        ArrayValidationError:
            If any entry fails validation.
    """
    items_schema = schema.get("items", {})
    allowed_fields = set(items_schema.get("properties", {}).get("field", {}).get("enum", []))
    allowed_orders = set(items_schema.get("properties", {}).get("order", {}).get("enum", ["asc", "desc"]))

    for i, item in enumerate(sorting):
        field = item.get("field")

        if not field or field not in allowed_fields:
            raise ArrayValidationError(i, f"Field '{field}' not in {allowed_fields}")

        order = item.get("order", "asc")

        if order not in allowed_orders:
            raise ArrayValidationError(i, f"Order '{order}' not in {allowed_orders}")

        extra_keys = set(item.keys()) - {"field", "order"}

        if extra_keys:
            raise ArrayValidationError(i, f"Unexpected key(s) provided: {extra_keys}")
