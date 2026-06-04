import re
from unittest.mock import patch

import pytest

from app.security.regex import (
    RegexTimeoutError,
    safe_compile_regex,
    timeout_signal,
)


class TestSafeCompileRegex:
    def test_valid_regex_returns_compiled_pattern(self):
        pattern = r"test"
        result = safe_compile_regex(pattern)

        assert result is not None
        assert result.pattern == pattern

    def test_valid_regex_with_special_characters(self):
        pattern = r"^[a-zA-Z0-9_]+$"
        result = safe_compile_regex(pattern)

        assert result is not None

    def test_invalid_regex_raises_value_error(self):
        pattern = r"[invalid"

        with pytest.raises(ValueError, match="Invalid regex"):
            safe_compile_regex(pattern)

    def test_safe_regex_matches_expected_text(self):
        pattern = r"\d+"
        compiled = safe_compile_regex(pattern)

        assert compiled.search("abc123def") is not None
        assert compiled.search("abcdef") is None


class TestRegexTimeoutSignal:
    def test_timeout_raises_regex_timeout_error(self):
        def long_running_regex():
            pattern = r"(a+)+b" + ("c" * 100)
            re.compile(pattern)

        with pytest.raises(RegexTimeoutError):
            with timeout_signal(seconds=0.00001):
                long_running_regex()

    def test_normal_execution_completes(self):
        def normal_task():
            return 42

        with timeout_signal(seconds=5.0):
            result = normal_task()

        assert result == 42

    def test_signals_not_available_silently_fallbacks(self):
        with patch("app.security.regex.signal") as mock_signal:
            mock_signal.signal.side_effect = AttributeError("Signals not available")

            with timeout_signal(seconds=1.0):
                result = 42

            assert result == 42
