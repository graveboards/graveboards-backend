"""
Test data factory patterns - generates test data programmatically.

This module provides factories for generating osu! API response data
programmatically without relying on static fixture JSON files.
Uses factory_boy for deterministic and customizable test data generation.
"""

from datetime import datetime
from typing import Any, Dict, List

import factory
from factory import Sequence, LazyAttribute, Faker



class BeatmapFactory(factory.Factory):
    """Factory for generating beatmap test data."""

    class Meta:
        model = dict

    id = Sequence(lambda n: 100000 + n)
    beatmapset_id = Sequence(lambda n: 50000 + n)
    version = Faker('lexify', text='???')
    creator = Faker('user_name')
    bpm = Sequence(lambda n: 60.0 + (n % 140))
    difficulty_rating = Sequence(lambda n: round(0.5 + (n % 9), 2))
    total_length = Sequence(lambda n: 60 + (n % 240))
    hit_length = LazyAttribute(lambda o: int(o.total_length * 0.9))
    mode = Sequence(lambda n: n % 4)
    status = Sequence(lambda n: ['ranked', 'loved', 'qualified', 'graveyard', 'pending', 'approved'][n % 6])

    difficulty_rating = LazyAttribute(lambda o: round(0.5 + (hash(str(o.id)) % 900) / 100.0, 2))
    playcount = Sequence(lambda n: n * 100 + 50)
    passcount = LazyAttribute(lambda o: int(o.playcount * 0.3 + hash(str(o.id)) % 100))
    created_at = LazyAttribute(lambda o: datetime.utcnow().isoformat() + '+00:00')
    updated_at = LazyAttribute(lambda o: datetime.utcnow().isoformat() + '+00:00')

    difficulty_rating = LazyAttribute(lambda o: round(0.5 + (o.id % 900) / 100.0, 2))
    playcount = Sequence(lambda n: n * 100 + 50)
    passcount = LazyAttribute(lambda o: int(o.playcount * 0.3 + (o.id % 100)))

    mode = Sequence(lambda n: n % 4)

    @LazyAttribute
    def beatmapset_id(self):
        return self.id // 2

    @LazyAttribute
    def version(self):
        return f'Factory {self.id}'

    @LazyAttribute
    def creator(self):
        return f'FactoryCreator{self.id}'

    @LazyAttribute
    def difficulty_rating(self):
        return round(0.5 + (self.id % 900) / 100.0, 2)

    @LazyAttribute
    def playcount(self):
        return self.id * 100 + 50

    @LazyAttribute
    def passcount(self):
        return int(self.playcount * 0.3 + (self.id % 100))


def generate_beatmap_data(
    count: int = 1,
    **overrides
) -> List[Dict[str, Any]]:
    """Generate beatmap test data with optional overrides."""
    return [BeatmapFactory.build(**overrides) for _ in range(count)]


def generate_user_data(
    count: int = 1,
    ruleset: str = "osu",
    **overrides
) -> List[Dict[str, Any]]:
    """Generate user/tester data with optional overrides."""
    data = []
    for i in range(count):
        user_id = 1000000 + i
        user_data = {
            "id": user_id,
            "username": f"FactoryUser{user_id}",
            "avatar_url": f"https://example.com/avatar{user_id}.png",
            "country_code": "US",
            "join_date": (datetime.utcnow().replace(year=2020) + __import__('datetime').timedelta(days=i*30)).isoformat() + "+00:00",
            "is_active": True,
            "statistics": {
                "pp": float(user_id * 10),
                "play_count": user_id * 100,
                "ranked_score": user_id * 100000,
                "total_score": user_id * 500000,
            },
            **overrides
        }
        data.append(user_data)
    return data


def generate_score_data(
    count: int = 1,
    ruleset: str = "osu",
    **overrides
) -> List[Dict[str, Any]]:
    """Generate score test data with optional overrides."""
    data = []
    for i in range(count):
        score_id = 5000000 + i
        user_id = 1000000 + i
        beatmap_id = 100000 + i
        score_data = {
            "id": score_id,
            "user_id": user_id,
            "beatmap_id": beatmap_id,
            "rank": ['SS', 'S', 'A', 'B', 'C', 'D'][i % 6],
            "score": 50000 + (i % 950000),
            "max_combo": 50 + (i % 950),
            "count_300": int((50 + (i % 950)) * 2.5),
            "count_100": int((50 + (i % 950)) * 0.3),
            "count_50": int((50 + (i % 950)) * 0.1),
            "count_miss": int((50 + (i % 950)) * 0.05),
            "passed": True,
            **overrides
        }
        data.append(score_data)
    return data


def generate_beatmapset_data(
    count: int = 1,
    **overrides
) -> List[Dict[str, Any]]:
    """Generate beatmapset test data with optional overrides."""
    data = []
    for i in range(count):
        beatmapset_id = 100000 + i
        beatmapset_data = {
            "id": beatmapset_id,
            "title": f"Factory Beatmapset {beatmapset_id}",
            "artist": f"Factory Artist {beatmapset_id}",
            "creator": f"FactoryCreator{beatmapset_id}",
            "status": ['ranked', 'loved', 'qualified', 'graveyard', 'pending', 'approved'][i % 6],
            "bpm": 120.0 + (i % 100),
            "difficulty_rating": round(0.5 + (beatmapset_id % 900) / 100.0, 2),
            **overrides
        }
        data.append(beatmapset_data)
    return data


def generate_beatmap_attributes_data(
    count: int = 1,
    **overrides
) -> List[Dict[str, Any]]:
    """Generate beatmap attributes test data with optional overrides."""
    data = []
    for i in range(count):
        beatmap_id = 100000 + i
        attrs_data = {
            "beatmap_id": beatmap_id,
            "difficulty": round(0.5 + (beatmap_id % 900) / 100.0, 2),
            "aim": round(0.5 + (i % 900) / 100.0, 2),
            "speed": round(0.5 + (i % 900) / 100.0, 2),
            "approach_rate": round(3.0 + (i % 7), 2),
            "circle_size": round(3.0 + (i % 4), 2),
            "drain": round(3.0 + (i % 7), 2),
            "overall": round(3.0 + (i % 7), 2),
            **overrides
        }
        data.append(attrs_data)
    return data
