"""Queue and Request fixture generator for search engine testing.

Generates diverse queue and request fixtures to enable comprehensive
testing of the search engine's QUEUES and REQUESTS scopes, including:
- Varied queue names and descriptions (for text search)
- Varied visibility and is_open states (for boolean filtering)
- Requests with varied statuses, comments, mv_checked states
- Cross-entity relationships (queues -> requests -> beatmapsets -> beatmaps)
- Profile associations (queue user_id -> profile filtering)

Request generation uses a pair-shuffling algorithm to ensure no duplicate
(queue_id, beatmapset_id) combinations, respecting the database's unique
constraint on those columns. Each request's user_id is set to the owner
of the requested beatmapset.
"""

import json
import random
from datetime import datetime, timezone, timedelta
from itertools import product
from pathlib import Path
from typing import Optional

from app.config import PROJECT_ROOT
from app.fixtures.bn_queue_comments import BN_QUEUE_COMMENTS as REQUEST_COMMENTS
from app.fixtures.queue_metadata import QUEUE_NAMES, QUEUE_DESCRIPTIONS
from app.fixtures.metadata_io import load_metadata, save_metadata

QUEUE_FIXTURES_PATH = PROJECT_ROOT / "instance" / "fixtures" / "queues"
REQUEST_FIXTURES_PATH = PROJECT_ROOT / "instance" / "fixtures" / "requests"

BLANK_COMMENT_CHANCE = 0.25

REQUEST_STATUSES = [-1, 0, 1]
REQUEST_STATUS_NAMES = ["rejected", "pending", "accepted"]


class QueueRequestFixtureGenerator:
    """Generates diverse queue and request fixtures for search testing."""

    def __init__(
        self,
        user_ids: list[int] = None,
        beatmapset_ids: list[int] = None,
        queue_ids: list[int] = None,
    ):
        self.user_ids = user_ids or self._load_existing_user_ids()
        self.beatmapset_ids = beatmapset_ids or self._load_existing_beatmapset_ids()
        self.queue_ids = queue_ids or self._load_existing_queue_ids()
        self._next_queue_id = max(self.queue_ids) + 1 if self.queue_ids else 1
        self._beatmapset_owners: dict[int, int] = self._load_beatmapset_owners()

    def _load_existing_user_ids(self) -> list[int]:
        users_path = PROJECT_ROOT / "instance" / "fixtures" / "users"
        user_ids = []
        if users_path.exists():
            for ruleset_dir in users_path.iterdir():
                if ruleset_dir.is_dir():
                    for f in ruleset_dir.glob("user_*.json"):
                        try:
                            uid = int(f.stem.split("_")[1])
                            user_ids.append(uid)
                        except (IndexError, ValueError):
                            pass
        return user_ids

    def _load_existing_beatmapset_ids(self) -> list[int]:
        bms_path = PROJECT_ROOT / "instance" / "fixtures" / "beatmapsets"
        bms_ids = []
        if bms_path.exists():
            for f in bms_path.glob("beatmapset_*.json"):
                try:
                    bid = int(f.stem.split("_")[1])
                    bms_ids.append(bid)
                except (IndexError, ValueError):
                    pass
        return bms_ids

    def _load_existing_queue_ids(self) -> list[int]:
        q_path = PROJECT_ROOT / "instance" / "fixtures" / "queues"
        q_ids = []
        if q_path.exists():
            for f in q_path.glob("queue_*.json"):
                try:
                    qid = int(f.stem.split("_")[1])
                    q_ids.append(qid)
                except (IndexError, ValueError):
                    pass
        return q_ids

    def _load_beatmapset_owners(self) -> dict[int, int]:
        """Load beatmapset data to build a mapping of beatmapset_id -> owner_user_id."""
        bms_path = PROJECT_ROOT / "instance" / "fixtures" / "beatmapsets"
        owners: dict[int, int] = {}
        if not bms_path.exists():
            return owners

        for f in bms_path.glob("beatmapset_*.json"):
            try:
                bid = int(f.stem.split("_")[1])
                with open(f) as fh:
                    data = json.load(fh)
                if "user_id" in data:
                    owners[bid] = data["user_id"]
            except (IndexError, ValueError, json.JSONDecodeError, KeyError):
                continue

        return owners

    def generate_queues(self, count: int = 10) -> list[dict]:
        """Generate diverse queue fixtures."""
        queues = []
        used_names = set()

        for i in range(count):
            queue_id = self._next_queue_id + i
            name = self._choose_name(used_names)
            used_names.add(name)

            user_id = random.choice(self.user_ids) if self.user_ids else 0
            is_open = random.choice([True, True, True, False])
            visibility = random.choice([0, 1, 2])

            queue = {
                "id": queue_id,
                "user_id": user_id,
                "name": name,
                "description": random.choice(QUEUE_DESCRIPTIONS),
                "is_open": is_open,
                "visibility": visibility,
                "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365)),
                "updated_at": datetime.now(timezone.utc),
            }
            queues.append(queue)

        return queues

    def generate_requests(
        self,
        queues: list[dict],
        count: int = 100,
    ) -> list[dict]:
        """Generate diverse request fixtures linked to queues and beatmapsets.

        Uses a pair-shuffling algorithm to ensure no duplicate (queue_id,
        beatmapset_id) combinations. Each request's user_id is set to the
        owner of the requested beatmapset.

        Raises:
            ValueError: If count exceeds the number of available (queue, beatmapset) pairs.
        """
        if not queues:
            return []

        if not self.beatmapset_ids:
            return []

        max_pairs = len(queues) * len(self.beatmapset_ids)
        if count > max_pairs:
            raise ValueError(
                f"Cannot generate {count} requests: only {max_pairs} unique "
                f"(queue, beatmapset) pairs available ({len(queues)} queues x "
                f"{len(self.beatmapset_ids)} beatmapsets). "
                f"Reduce request count or increase queue/beatmapset fixtures."
            )

        pairs = list(product(queues, self.beatmapset_ids))
        random.shuffle(pairs)
        selected_pairs = pairs[:count]

        requests = []
        for i, (queue, beatmapset_id) in enumerate(selected_pairs, start=1):
            owner_id = self._beatmapset_owners.get(beatmapset_id, queue["user_id"])

            status = random.choice(REQUEST_STATUSES)
            mv_checked = random.choice([True, False])
            if random.random() < BLANK_COMMENT_CHANCE:
                comment = ""
            else:
                comment = random.choice(REQUEST_COMMENTS)

            request = {
                "id": i,
                "user_id": owner_id,
                "beatmapset_id": beatmapset_id,
                "queue_id": queue["id"],
                "comment": comment,
                "mv_checked": mv_checked,
                "status": status,
                "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180)),
                "updated_at": datetime.now(timezone.utc),
            }
            requests.append(request)

        return requests

    def save_queues(self, queues: list[dict]) -> Path:
        """Save queue fixtures to instance fixtures."""
        QUEUE_FIXTURES_PATH.mkdir(parents=True, exist_ok=True)

        for queue in queues:
            filepath = QUEUE_FIXTURES_PATH / f"queue_{queue['id']}.json"
            serializable_queue = {
                k: v.isoformat() if isinstance(v, datetime) else v for k, v in queue.items()
            }
            with open(filepath, "w") as f:
                json.dump(serializable_queue, f, indent=2)

        metadata = load_metadata()
        metadata["samples"]["queues"]["count"] = len(queues)
        metadata["samples"]["queues"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(metadata)

        return QUEUE_FIXTURES_PATH

    def save_requests(self, requests: list[dict]) -> Path:
        """Save request fixtures to instance fixtures."""
        REQUEST_FIXTURES_PATH.mkdir(parents=True, exist_ok=True)

        for request in requests:
            filepath = REQUEST_FIXTURES_PATH / f"request_{request['id']}.json"
            serializable_request = {
                k: v.isoformat() if isinstance(v, datetime) else v for k, v in request.items()
            }
            with open(filepath, "w") as f:
                json.dump(serializable_request, f, indent=2)

        metadata = load_metadata()
        metadata["samples"]["requests"]["count"] = len(requests)
        metadata["samples"]["requests"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(metadata)

        return REQUEST_FIXTURES_PATH

    def _choose_name(self, used_names: set) -> str:
        """Choose a queue name not already used."""
        available = [n for n in QUEUE_NAMES if n not in used_names]
        if not available:
            available = QUEUE_NAMES
        return random.choice(available)

    def generate_comprehensive(
        self,
        queue_count: int = 10,
        request_count: int = 100,
    ) -> tuple[list[dict], list[dict]]:
        """Generate both queues and requests with cross-entity relationships."""
        queues = self.generate_queues(queue_count)
        requests = self.generate_requests(queues, request_count)
        return queues, requests
