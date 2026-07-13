import pytest

from app.observability.metrics.middleware import _reconstruct_nested_params


class TestReconstructNestedParams:
    """Test _reconstruct_nested_params helper."""

    def test_single_bracket_key(self):
        """Test a single bracket-notation key reconstructs correctly."""
        params = {"filters[id][eq]": "42"}
        result = _reconstruct_nested_params(params)
        assert result == {"filters": {"id": {"eq": "42"}}}

    def test_no_bracket_keys(self):
        """Test that all-flat params are returned unchanged."""
        params = {"limit": "10", "offset": "0"}
        result = _reconstruct_nested_params(params)
        assert result == params

    def test_mixed_flat_and_bracket(self):
        """Test mixed flat and bracket keys coexist."""
        params = {"limit": "10", "filters[user_id][eq]": "123", "offset": "0"}
        expected = {"limit": "10", "filters": {"user_id": {"eq": "123"}}, "offset": "0"}
        assert _reconstruct_nested_params(params) == expected

    def test_three_level_nesting(self):
        """Test three-level bracket nesting."""
        params = {"a[b][c][d]": "value"}
        expected = {"a": {"b": {"c": {"d": "value"}}}}
        assert _reconstruct_nested_params(params) == expected

    def test_empty_brackets_not_matched(self):
        """Test that empty brackets do not match the bracket pattern."""
        params = {"filters[]": "value", "normal": "thing"}
        result = _reconstruct_nested_params(params)
        assert result == params

    def test_duplicate_path_merging(self):
        """Test that duplicate paths merge into one nested object."""
        params = {"include[a][x]": "1", "include[a][y]": "2", "include[b]": "3"}
        expected = {"include": {"a": {"x": "1", "y": "2"}, "b": "3"}}
        assert _reconstruct_nested_params(params) == expected

    def test_full_query_params_reconstruction(self):
        """Test reconstruction with a realistic full query params dict."""
        params = {
            "filters[comment][neq]": "hi",
            "filters[queue_id][eq]": "1",
            "include[queue][id]": "false",
            "include[queue][name]": "true",
            "limit": "50",
            "offset": "0",
            "reversed": "false",
            "search_mode": "simple",
            "search_relevance": "false",
        }
        result = _reconstruct_nested_params(params)
        assert result["filters"] == {"comment": {"neq": "hi"}, "queue_id": {"eq": "1"}}
        assert result["include"] == {"queue": {"id": "false", "name": "true"}}
        assert result["limit"] == "50"
        assert result["offset"] == "0"
        assert result["reversed"] == "false"
        assert result["search_mode"] == "simple"
        assert result["search_relevance"] == "false"

    def test_bracket_key_with_special_characters(self):
        """Test bracket keys with underscores and hyphens."""
        params = {"filters[user_id][not-eq]": "123"}
        result = _reconstruct_nested_params(params)
        assert result == {"filters": {"user_id": {"not-eq": "123"}}}

    def test_empty_params(self):
        """Test that empty params dict returns empty dict."""
        assert _reconstruct_nested_params({}) == {}
