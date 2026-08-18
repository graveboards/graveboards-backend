import pytest

from app.config import Config, ServiceSettings


class TestServiceConfig:
    """Test daemon service configuration parsing."""

    def test_service_settings_defaults_when_unset(self, monkeypatch) -> None:
        """Test that service settings fall back to defaults when unset."""
        for name in (
            "SERVICES_PROFILE_FETCHER_ENABLED",
            "SERVICES_PROFILE_FETCHER_INTERVAL_HOURS",
            "SERVICES_SCORE_FETCHER_ENABLED",
            "SERVICES_SCORE_FETCHER_INTERVAL_HOURS",
            "SERVICES_QUEUE_REQUEST_HANDLER_ENABLED",
            "SERVICES_RULE_VALIDATION_ENABLED",
        ):
            monkeypatch.delenv(name, raising=False)

        config = Config()

        assert config.SERVICES["profile_fetcher"] == ServiceSettings(
            enabled=True, interval_hours=168.0
        )
        assert config.SERVICES["score_fetcher"] == ServiceSettings(
            enabled=True, interval_hours=24.0
        )
        assert config.SERVICES["queue_request_handler"] == ServiceSettings(enabled=True)
        assert config.SERVICES["rule_validation"] == ServiceSettings(enabled=True)

    def test_service_settings_override_when_set(self, monkeypatch) -> None:
        """Test that service settings reflect explicitly set environment variables."""
        monkeypatch.setenv("SERVICES_PROFILE_FETCHER_ENABLED", "false")
        monkeypatch.setenv("SERVICES_PROFILE_FETCHER_INTERVAL_HOURS", "72.5")
        monkeypatch.setenv("SERVICES_SCORE_FETCHER_ENABLED", "false")
        monkeypatch.setenv("SERVICES_SCORE_FETCHER_INTERVAL_HOURS", "6")
        monkeypatch.setenv("SERVICES_QUEUE_REQUEST_HANDLER_ENABLED", "0")
        monkeypatch.setenv("SERVICES_RULE_VALIDATION_ENABLED", "1")

        config = Config()

        assert config.SERVICES["profile_fetcher"] == ServiceSettings(
            enabled=False, interval_hours=72.5
        )
        assert config.SERVICES["score_fetcher"] == ServiceSettings(
            enabled=False, interval_hours=6.0
        )
        assert config.SERVICES["queue_request_handler"] == ServiceSettings(enabled=False)
        assert config.SERVICES["rule_validation"] == ServiceSettings(enabled=True)

    def test_invalid_interval_raises_value_error(self, monkeypatch) -> None:
        """Test that an invalid interval raises a clear error."""
        monkeypatch.setenv("SERVICES_PROFILE_FETCHER_INTERVAL_HOURS", "not-a-number")

        with pytest.raises(ValueError, match="SERVICES_PROFILE_FETCHER_INTERVAL_HOURS"):
            Config()
