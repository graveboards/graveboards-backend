import pytest
import os
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

from app.spec.load import (
    load_spec,
    _build_spec,
    _apply_mutations,
    _current_build_options,
    _get_latest_spec_mtime,
)


class TestLoadSpec:
    """Test OpenAPI spec loading."""

    @pytest.fixture
    def mock_yaml_full_load(self):
        """Mock yaml.full_load."""
        with patch("app.spec.load.yaml.full_load") as mock:
            yield mock

    @pytest.fixture
    def mock_resolve_refs(self):
        """Mock connexion.spec.resolve_refs."""
        with patch("app.spec.load.resolve_refs") as mock:
            yield mock

    @pytest.fixture
    def mock_pickle(self):
        """Mock pickle module."""
        with patch("app.spec.load.pickle") as mock:
            yield mock

    @pytest.fixture
    def mock_env(self):
        """Mock ENV configuration."""
        with patch("app.spec.load.ENV") as mock:
            yield mock

    @pytest.fixture
    def mock_os_path_exists(self):
        """Mock os.path.exists."""
        with patch("app.spec.load.os.path.exists") as mock:
            yield mock

    @pytest.fixture
    def mock_os_path_getmtime(self):
        """Mock os.path.getmtime."""
        with patch("app.spec.load.os.path.getmtime") as mock:
            yield mock

    @pytest.fixture
    def mock_os_walk(self):
        """Mock os.walk."""
        with patch("app.spec.load.os.walk") as mock:
            yield mock

    def test_load_spec_no_cache_rebuilds(self, mock_yaml_full_load, mock_resolve_refs):
        """Test that load_spec rebuilds when cache doesn't exist."""
        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}

        with patch("app.spec.load.os.path.exists", return_value=False):
            with patch("app.spec.load._build_spec") as mock_build:
                mock_build.return_value = {"spec": "data"}
                result = load_spec()

                assert result == {"spec": "data"}
                mock_build.assert_called_once()

    def test_load_spec_prod_mode_returns_cached(self, mock_pickle):
        """Test that prod mode returns cached spec."""
        from app.enums import Env

        mock_pickle.load.return_value = {"spec": "cached_spec"}

        with patch("app.spec.load.os.path.exists", return_value=True):
            with patch("app.spec.load.ENV", Env.PROD):
                with patch("builtins.open", mock_open(read_data="data")):
                    result = load_spec()

        assert result == "cached_spec"

    def test_load_spec_non_prod_invalidates_on_mtime(self, mock_yaml_full_load, mock_resolve_refs, mock_os_path_getmtime, mock_pickle, mock_os_walk):
        """Test that non-prod mode invalidates cache on mtime."""
        from app.enums import Env

        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}
        mock_os_walk.return_value = [
            ("/spec", [], ["a.yaml", "b.yml"]),
        ]
        mock_os_path_getmtime.side_effect = [100, 180, 200]  # cache=100, latest=200

        mock_pickle.load.return_value = {
            "spec": "old_spec",
            "build_options": {"env": Env.DEV, "disable_security": False}
        }

        with patch("app.spec.load.os.path.exists", return_value=True):
            with patch("app.spec.load.ENV", Env.DEV):
                with patch("builtins.open", mock_open(read_data="data")):
                    with patch("app.spec.load._build_spec") as mock_build:
                        mock_build.return_value = {"spec": "new_spec"}
                        result = load_spec()

        assert result == {"spec": "new_spec"}
        mock_build.assert_called_once()

    def test_load_spec_non_prod_invalidates_on_options(self, mock_yaml_full_load, mock_resolve_refs, mock_os_path_getmtime, mock_pickle, mock_os_walk):
        """Test that non-prod mode invalidates cache on build options."""
        from app.enums import Env

        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}
        mock_os_walk.return_value = [
            ("/spec", [], ["a.yaml", "b.yml"]),
        ]
        mock_os_path_getmtime.side_effect = [200, 80, 90]  # cache=200, latest=90

        mock_pickle.load.return_value = {
            "spec": "old_spec",
            "build_options": {"env": Env.DEV, "disable_security": False}
        }

        with patch("app.spec.load.os.path.exists", return_value=True):
            with patch("app.spec.load.ENV", Env.DEV):
                with patch("builtins.open", mock_open(read_data="data")):
                    with patch("app.spec.load._current_build_options", return_value={"env": Env.DEV, "disable_security": True}):
                        with patch("app.spec.load._build_spec") as mock_build:
                            mock_build.return_value = {"spec": "new_spec"}
                            result = load_spec()

        assert result == {"spec": "new_spec"}
        mock_build.assert_called_once()

    def test_build_spec_loads_yaml(self, mock_yaml_full_load, mock_resolve_refs):
        """Test that _build_spec loads YAML spec."""
        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}

        with patch("app.spec.load.open", mock_open(read_data="spec: data")):
            with patch("app.spec.load.SPEC_DIR", "/spec"):
                result = _build_spec()

        assert "components" in result
        mock_yaml_full_load.assert_called_once()

    def test_build_spec_resolves_refs(self, mock_yaml_full_load, mock_resolve_refs):
        """Test that _build_spec resolves refs."""
        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {"resolved": True}}}

        with patch("app.spec.load.open", mock_open(read_data="spec: data")):
            with patch("app.spec.load.SPEC_DIR", "/spec"):
                result = _build_spec()

        assert result == {"components": {"schemas": {"resolved": True}}}
        mock_resolve_refs.assert_called_once()

    def test_build_spec_applies_mutations(self, mock_yaml_full_load, mock_resolve_refs):
        """Test that _build_spec applies mutations."""
        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}

        with patch("app.spec.load.open", mock_open(read_data="spec: data")):
            with patch("app.spec.load.SPEC_DIR", "/spec"):
                with patch("app.spec.load.populate_shallow_refs") as mock_populate:
                    result = _build_spec()

        mock_populate.assert_called_once()

    def test_build_spec_writes_cache(self, mock_yaml_full_load, mock_resolve_refs, mock_pickle):
        """Test that _build_spec writes cache file."""
        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}
        mock_pickle.dump.return_value = None

        with patch("app.spec.load.open", mock_open(read_data="spec: data")):
            with patch("app.spec.load.SPEC_DIR", "/spec"):
                with patch("app.spec.load.pickle.dump") as mock_dump:
                    with patch("app.spec.load._current_build_options", return_value={}):
                        result = _build_spec()

        assert mock_dump.called

    def test_apply_mutations_populates_shallow_refs(self, mock_yaml_full_load, mock_resolve_refs):
        """Test that _apply_mutations populates shallow refs."""
        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}

        spec = {"components": {"schemas": {}}}

        with patch("app.spec.load.populate_shallow_refs") as mock_populate:
            _apply_mutations(spec)

        mock_populate.assert_called_once_with(spec)

    def test_apply_mutations_removes_security_when_disabled(self, mock_yaml_full_load, mock_resolve_refs):
        """Test that security is removed when disabled."""
        from app.enums import Env

        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}

        spec = {
            "components": {"schemas": {}},
            "security": [{"oauth": []}],
            "paths": {
                "/test": {
                    "get": {"security": [{"oauth": []}]}
                }
            }
        }

        with patch("app.spec.load.populate_shallow_refs"):
            with patch("app.spec.load.DISABLE_SECURITY", True):
                with patch("app.spec.load.ENV", Env.DEV):
                    _apply_mutations(spec)

        assert "security" not in spec
        assert "security" not in spec["paths"]["/test"]["get"]

    def test_apply_mutations_keeps_security_when_enabled(self, mock_yaml_full_load, mock_resolve_refs):
        """Test that security is kept when enabled."""
        from app.enums import Env

        spec = {
            "components": {"schemas": {}},
            "security": [{"oauth": []}],
            "paths": {
                "/test": {
                    "get": {"security": [{"oauth": []}]}
                }
            }
        }

        with patch("app.spec.load.populate_shallow_refs"):
            with patch("app.spec.load.DISABLE_SECURITY", False):
                with patch("app.spec.load.ENV", Env.PROD):
                    _apply_mutations(spec)

        assert "security" in spec
        assert "security" in spec["paths"]["/test"]["get"]

    def test_current_build_options_returns_env_and_security(self, mock_yaml_full_load, mock_resolve_refs):
        """Test that _current_build_options returns current options."""
        from app.enums import Env

        with patch("app.spec.load.ENV", Env.DEV):
            with patch("app.spec.load.DISABLE_SECURITY", True):
                result = _current_build_options()

        assert result["env"] == Env.DEV
        assert result["disable_security"] is True

    def test_get_latest_spec_mtime_scans_yaml_files(self, mock_os_walk):
        """Test that _get_latest_spec_mtime scans all YAML files."""
        mock_os_walk.return_value = [
            ("/spec", [], ["a.yaml", "b.yml", "c.txt"]),
        ]

        with patch("app.spec.load.os.path.getmtime") as mock_getmtime:
            mock_getmtime.side_effect = [100, 200, 50]
            result = _get_latest_spec_mtime()

        assert result == 200
        mock_getmtime.assert_any_call("/spec/a.yaml")
        mock_getmtime.assert_any_call("/spec/b.yml")
        call_args = [call[0][0] for call in mock_getmtime.call_args_list]
        assert "/spec/c.txt" not in call_args

    def test_get_latest_spec_mtime_returns_zero_when_no_files(self, mock_os_walk):
        """Test that _get_latest_spec_mtime returns 0 when no files."""
        mock_os_walk.return_value = []

        result = _get_latest_spec_mtime()

        assert result == 0.0

    def test_get_latest_spec_mtime_scans_recursively(self, mock_os_walk):
        """Test that _get_latest_spec_mtime scans recursively."""
        mock_os_walk.return_value = [
            ("/spec", ["subdir"], []),
            ("/spec/subdir", [], ["nested.yaml"]),
        ]

        with patch("app.spec.load.os.path.getmtime") as mock_getmtime:
            mock_getmtime.return_value = 150
            result = _get_latest_spec_mtime()

        mock_getmtime.assert_any_call("/spec/subdir/nested.yaml")

    def test_get_latest_spec_mtime_skips_non_yaml(self, mock_os_walk):
        """Test that _get_latest_spec_mtime skips non-YAML files."""
        mock_os_walk.return_value = [
            ("/spec", [], ["a.yaml", "b.json", "c.txt", "d.yml"]),
        ]

        with patch("app.spec.load.os.path.getmtime") as mock_getmtime:
            mock_getmtime.side_effect = [100, 150]
            result = _get_latest_spec_mtime()

        assert result == 150
        call_args = [call[0][0] for call in mock_getmtime.call_args_list]
        assert "/spec/a.yaml" in call_args
        assert "/spec/d.yml" in call_args
        assert "/spec/b.json" not in call_args
        assert "/spec/c.txt" not in call_args

    def test_load_spec_with_existing_cache(self, mock_yaml_full_load, mock_resolve_refs, mock_pickle):
        """Test that load_spec uses existing cache."""
        mock_pickle.load.return_value = {"spec": "cached"}

        with patch("app.spec.load.os.path.exists", return_value=True):
            with patch("app.spec.load._build_spec") as mock_build:
                result = load_spec()

        assert result == "cached"
        mock_build.assert_not_called()
