from typing import Iterable

from app.text import align_center, justify
from app.database import PostgresqlDB, db_lifespan
from app.database.status import StatusTarget


@db_lifespan
async def cmd_status(db: PostgresqlDB, target: StatusTarget):
    status = await db.status(target)
    print_status(status)


def print_status(status: dict):
    target = status.pop("target").upper()
    row_width = 30

    print("=" * row_width)
    print(align_center(f"STATUS {target}", row_width))
    print("=" * row_width)

    for k, v in status.items():
        if isinstance(v, Iterable) and not isinstance(v, (str, bytes)):
            raise NotImplementedError
        else:
            print(justify(k, v, width=row_width))

    print("=" * row_width)
