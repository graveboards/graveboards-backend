"""Queue and Request fixture generator for search engine testing.

Generates diverse queue and request fixtures to enable comprehensive
testing of the search engine's QUEUES and REQUESTS scopes, including:
- Varied queue names and descriptions (for text search)
- Varied visibility and is_open states (for boolean filtering)
- Requests with varied statuses, comments, mv_checked states
- Cross-entity relationships (queues -> requests -> beatmapsets -> beatmaps)
- Profile associations (queue user_id -> profile filtering)
"""
import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from app.config import PROJECT_ROOT
from app.fixtures.bn_queue_comments import BN_QUEUE_COMMENTS as REQUEST_COMMENTS
from app.fixtures.queue_metadata import QUEUE_NAMES, QUEUE_DESCRIPTIONS
from app.fixtures.utils import load_metadata, save_metadata

QUEUE_FIXTURES_PATH = PROJECT_ROOT / "instance" / "fixtures" / "queues"
REQUEST_FIXTURES_PATH = PROJECT_ROOT / "instance" / "fixtures" / "requests"
SEEDING_QUEUES_PATH = PROJECT_ROOT / "app" / "database" / "seeding" / "fixtures" / "queues.json"
SEEDING_REQUESTS_PATH = PROJECT_ROOT / "app" / "database" / "seeding" / "fixtures" / "requests.json"

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
        if not user_ids:
            user_ids = [4098393, 5099768, 6064571, 7716455, 11422420, 16219092]
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
        if not bms_ids:
            bms_ids = [2387557, 623475, 1034724, 1895918, 2362400, 2344790]
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
        if not q_ids:
            q_ids = [1, 2]
        return q_ids

    def generate_queues(self, count: int = 50) -> list[dict]:
        """Generate diverse queue fixtures."""
        queues = []
        used_names = set()

        for i in range(count):
            queue_id = self._next_queue_id + i
            name = self._choose_name(used_names)
            used_names.add(name)

            user_id = random.choice(self.user_ids)
            is_open = random.choice([True, True, True, False])
            visibility = random.choice([0, 1, 2])

            queue = {
                "id": queue_id,
                "user_id": user_id,
                "name": name,
                "description": random.choice(QUEUE_DESCRIPTIONS),
                "is_open": is_open,
                "visibility": visibility,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365))).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            queues.append(queue)

        return queues

    def generate_requests(
        self,
        queues: list[dict],
        count: int = 100,
    ) -> list[dict]:
        """Generate diverse request fixtures linked to queues and beatmapsets."""
        requests = []
        used_combinations = set()

        for i in range(count):
            queue = random.choice(queues)
            queue_id = queue["id"]

            if not self.beatmapset_ids:
                continue

            beatmapset_id = random.choice(self.beatmapset_ids)
            combination = (beatmapset_id, queue_id)

            if combination in used_combinations:
                continue
            used_combinations.add(combination)

            status = random.choice(REQUEST_STATUSES)
            mv_checked = random.choice([True, False])
            if random.random() < BLANK_COMMENT_CHANCE:
                comment = ""
            else:
                comment = random.choice(REQUEST_COMMENTS)

            request = {
                "id": i + 1,
                "user_id": queue["user_id"],
                "beatmapset_id": beatmapset_id,
                "queue_id": queue_id,
                "comment": comment,
                "mv_checked": mv_checked,
                "status": status,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180))).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            requests.append(request)

        return requests

    def save_queues(self, queues: list[dict]) -> Path:
        """Save queue fixtures to instance fixtures and seeding fixtures."""
        QUEUE_FIXTURES_PATH.mkdir(parents=True, exist_ok=True)

        for queue in queues:
            filepath = QUEUE_FIXTURES_PATH / f"queue_{queue['id']}.json"
            with open(filepath, "w") as f:
                json.dump(queue, f, indent=2)

        combined = queues
        with open(SEEDING_QUEUES_PATH, "w") as f:
            json.dump(combined, f, indent=2)

        metadata = load_metadata()
        metadata["samples"]["queues"]["count"] = len(queues)
        metadata["samples"]["queues"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(metadata)

        return QUEUE_FIXTURES_PATH

    def save_requests(self, requests: list[dict]) -> Path:
        """Save request fixtures to instance fixtures and seeding fixtures."""
        REQUEST_FIXTURES_PATH.mkdir(parents=True, exist_ok=True)

        for request in requests:
            filepath = REQUEST_FIXTURES_PATH / f"request_{request['id']}.json"
            with open(filepath, "w") as f:
                json.dump(request, f, indent=2)

        combined = requests
        with open(SEEDING_REQUESTS_PATH, "w") as f:
            json.dump(combined, f, indent=2)

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
        queue_count: int = 50,
        request_count: int = 100,
    ) -> tuple[list[dict], list[dict]]:
        """Generate both queues and requests with cross-entity relationships."""
        queues = self.generate_queues(queue_count)
        requests = self.generate_requests(queues, request_count)
        return queues, requests


def generate_and_save(
    queue_count: int = 50,
    request_count: int = 100,
    user_ids: list[int] = None,
    beatmapset_ids: list[int] = None,
) -> tuple[list[dict], list[dict]]:
    """Generate and save queue/request fixtures."""
    generator = QueueRequestFixtureGenerator(
        user_ids=user_ids,
        beatmapset_ids=beatmapset_ids,
    )
    queues, requests = generator.generate_comprehensive(queue_count, request_count)
    generator.save_queues(queues)
    generator.save_requests(requests)
    return queues, requests
