from starlette.responses import Response


def build_pagination_response(
    data: list,
    total: int,
    limit: int,
    offset: int,
    request_url: str,
) -> tuple[list, int, dict]:
    """Build a paginated response with headers.

    Returns: (data, status_code, headers)
    """
    headers = {
        "Content-Type": "application/json",
        "X-Total-Count": str(total),
        "X-Page-Size": str(limit),
    }

    links = []
    base = request_url.rsplit("?", 1)[0]

    if offset + limit < total:
        next_offset = offset + limit
        links.append(f'<{base}?offset={next_offset}&limit={limit}>; rel="next"')

    if offset > 0:
        prev_offset = max(0, offset - limit)
        links.append(f'<{base}?offset={prev_offset}&limit={limit}>; rel="prev"')

    if links:
        headers["Link"] = ", ".join(links)

    return data, 200, headers
