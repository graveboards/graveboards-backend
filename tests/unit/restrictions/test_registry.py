import pytest

from app.database.restrictions.registry import (
    RESTRICTION_REGISTRY,
    RESTRICTION_TIERS,
    get_validator,
    get_validator_tier,
    get_validators_for_tier,
    get_supported_versions,
    register_validator,
)
from app.database.restrictions.base import RestrictionBase


class TestRegistryAllValidators:
    @pytest.mark.unit
    def test_tier1_validators_registered(self):
        assert "rate_limit" in RESTRICTION_REGISTRY
        assert "cooldown" in RESTRICTION_REGISTRY
        assert "blacklist" in RESTRICTION_REGISTRY

    @pytest.mark.unit
    def test_tier2_validators_registered(self):
        tier2_types = [
            "beatmap_duration", "beatmap_star_rating",
            "beatmap_ar_range", "beatmap_od_range",
            "beatmap_hp_range", "beatmap_cs_range",
            "beatmap_drain_range", "beatmap_bpm",
            "beatmap_genre", "beatmap_language",
            "beatmap_mode", "beatmap_difficulty_count",
            "beatmap_storyboard", "beatmap_video",
            "beatmap_tags", "beatmap_length",
            "beatmap_combination",
        ]
        for t in tier2_types:
            assert t in RESTRICTION_REGISTRY, f"{t} not in registry"

    @pytest.mark.unit
    def test_tier_assignments_correct(self):
        assert RESTRICTION_TIERS["rate_limit"] == 1
        assert RESTRICTION_TIERS["cooldown"] == 1
        assert RESTRICTION_TIERS["blacklist"] == 1
        assert RESTRICTION_TIERS["beatmap_duration"] == 2
        assert RESTRICTION_TIERS["beatmap_star_rating"] == 2
        assert RESTRICTION_TIERS["beatmap_bpm"] == 2
        assert RESTRICTION_TIERS["beatmap_genre"] == 2
        assert RESTRICTION_TIERS["beatmap_mode"] == 2

    @pytest.mark.unit
    def test_get_validator_returns_correct_class(self):
        cls = get_validator("beatmap_duration")
        assert cls is not None
        assert cls.restriction_type == "beatmap_duration"

    @pytest.mark.unit
    def test_get_validator_returns_none_for_unknown(self):
        assert get_validator("nonexistent") is None

    @pytest.mark.unit
    def test_get_validator_tier(self):
        assert get_validator_tier("rate_limit") == 1
        assert get_validator_tier("beatmap_duration") == 2
        assert get_validator_tier("nonexistent") is None

    @pytest.mark.unit
    def test_get_validators_for_tier(self):
        tier1 = get_validators_for_tier(1)
        assert "rate_limit" in tier1
        assert "cooldown" in tier1
        assert "blacklist" in tier1

        tier2 = get_validators_for_tier(2)
        assert "beatmap_duration" in tier2
        assert "beatmap_star_rating" in tier2
        assert "rate_limit" not in tier2

    @pytest.mark.unit
    def test_register_validator(self):
        class FakeValidator(RestrictionBase):
            restriction_type = "fake_test_type"

        register_validator("fake_test_type", FakeValidator, tier=2)
        assert "fake_test_type" in RESTRICTION_REGISTRY
        assert RESTRICTION_TIERS["fake_test_type"] == 2
        assert get_validator("fake_test_type") is FakeValidator

        RESTRICTION_REGISTRY.pop("fake_test_type", None)
        RESTRICTION_TIERS.pop("fake_test_type", None)

    @pytest.mark.unit
    def test_get_supported_versions(self):
        versions = get_supported_versions("rate_limit")
        assert versions is not None
        assert "1.0" in versions

    @pytest.mark.unit
    def test_get_supported_versions_unknown(self):
        assert get_supported_versions("nonexistent") is None

    @pytest.mark.unit
    def test_all_validators_have_supported_versions(self):
        for type_name in RESTRICTION_REGISTRY:
            versions = get_supported_versions(type_name)
            assert versions is not None, f"{type_name} has no supported versions"
            assert "1.0" in versions, f"{type_name} doesn't support version 1.0"
