import re

import pytest

from app.security.regex import safe_compile_regex


@pytest.mark.asyncio
class TestSafeCompileRegex:
    async def test_valid_regex_returns_compiled_pattern(self):
        pattern = r"test"
        result = await safe_compile_regex(pattern)

        assert result is not None
        assert result.pattern == pattern

    async def test_valid_regex_with_special_characters(self):
        pattern = r"^[a-zA-Z0-9_]+$"
        result = await safe_compile_regex(pattern)

        assert result is not None

    async def test_invalid_regex_returns_none(self):
        pattern = r"[invalid"
        result = await safe_compile_regex(pattern)
        assert result is None

    async def test_safe_regex_matches_expected_text(self):
        compiled = await safe_compile_regex(r"\d+")
        assert compiled is not None
        assert compiled.search("abc123def") is not None
        assert compiled.search("abcdef") is None

    async def test_timeout_returns_none(self):
        pattern = r"(a+)+b"
        sample = "a" * 27
        result = await safe_compile_regex(pattern, timeout=0.01, sample=sample)
        assert result is None
