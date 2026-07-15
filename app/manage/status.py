from typing import Iterable

from app.text import align_center, justify
from app.database import PostgresqlDB, db_lifespan
from app.database.status import StatusTarget


@db_lifespan
async def cmd_status(db: PostgresqlDB, target: StatusTarget):
    status = await db.status(target)
    print_status(status)


def _format_value(v, width: int, prefix: str = "") -> str:
    if isinstance(v, dict):
        return f"{prefix}[dict with {len(v)} items]"
    elif isinstance(v, Iterable) and not isinstance(v, (str, bytes)):
        return f"{prefix}{list(v)}"
    else:
        return f"{prefix}{v}"


def print_status(status: dict):
    target = status.pop("target").upper()
    row_width = 30

    print("=" * row_width)
    print(align_center(f"STATUS {target}", row_width))
    print("=" * row_width)

    for k, v in status.items():
        if isinstance(v, dict):
            print(justify(k, f"[dict with {len(v)} items]", width=row_width))
            for sub_k, sub_v in v.items():
                sub_line = f"  {sub_k}: {_format_value(sub_v, row_width, prefix='')}"
                if len(sub_line) > row_width:
                    sub_line = sub_line[: row_width - 1] + "…"
                print(sub_line)
        elif isinstance(v, Iterable) and not isinstance(v, (str, bytes)):
            print(justify(k, f"[{len(v)} items]", width=row_width))
        else:
            print(justify(k, str(v), width=row_width))

    print("=" * row_width)
