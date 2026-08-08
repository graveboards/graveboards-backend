"""Tests for app.spec.load — OpenAPI spec loading with environment-aware caching."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.spec.load import (
    _apply_mutations,
    _build_spec,
    _current_build_options,
    _get_latest_spec_mtime,
    load_spec,
)


@pytest.fixture(autouse=True)
def _clear_spec_lru_cache() -> None:
    """Clear the _get_spec_cached LRU cache between tests to prevent cross-test leakage."""
    from app.spec.schema import _get_spec_cached

    _get_spec_cached.cache_clear()


class TestLoadSpec:
    """Test OpenAPI spec loading."""

    @pytest.fixture
    def mock_yaml_full_load(self) -> Any:
        with patch("app.spec.load.yaml.full_load") as mock:
            yield mock

    @pytest.fixture
    def mock_resolve_refs(self) -> Any:
        with patch("app.spec.load.resolve_refs") as mock:
            yield mock

    @pytest.fixture
    def mock_pickle(self) -> Any:
        with patch("app.spec.load.pickle") as mock:
            yield mock

    @pytest.fixture
    def mock_env(self) -> Any:
        with patch("app.spec.load.ENV") as mock:
            yield mock

    @pytest.fixture
    def mock_cache_exists(self) -> Any:
        """Patch Path.exists on the cache file to return True."""
        with patch("app.spec.load.Path") as mock_path_cls:
            mock_cache_file = MagicMock()
            mock_cache_file.exists.return_value = True
            mock_path_cls.return_value = mock_cache_file
            mock_cache_file.__truediv__ = lambda self, other: Path(other)
            yield mock_cache_file

    # ------------------------------------------------------------------
    # load_spec() — cache missing → rebuild
    # ------------------------------------------------------------------

    def test_load_spec_no_cache_rebuilds(
        self, mock_yaml_full_load: Any, mock_resolve_refs: Any
    ) -> None:
        """load_spec rebuilds when cache doesn't exist."""
        with patch("app.spec.load._build_spec") as mock_build:
            mock_build.return_value = {"spec": "data"}
            with patch("app.spec.load.Path") as mock_path_cls:
                mock_cache_file = MagicMock()
                mock_cache_file.exists.return_value = False
                mock_path_cls.return_value = mock_cache_file

                result = load_spec()

            assert result == {"spec": "data"}
            mock_build.assert_called_once()

    # ------------------------------------------------------------------
    # load_spec() — prod mode → return cached
    # ------------------------------------------------------------------

    def test_load_spec_prod_mode_returns_cached(self, mock_pickle: Any) -> None:
        """In prod mode, load_spec returns the cached spec directly."""
        from app.enums import Env

        mock_pickle.load.return_value = {"spec": "cached_spec", "build_options": {}}

        with patch("app.spec.load.ENV", Env.PROD), patch("app.spec.load.Path") as mock_path_cls:
            mock_cache_file = MagicMock()
            mock_cache_file.exists.return_value = True
            mock_cache_file.open.return_value.__enter__.return_value = MagicMock()
            mock_path_cls.return_value = mock_cache_file

            result = load_spec()

        assert result == "cached_spec"

    def test_load_spec_with_existing_cache(
        self, mock_yaml_full_load: Any, mock_resolve_refs: Any, mock_pickle: Any
    ) -> None:
        """load_spec uses existing valid cache in prod mode."""
        from app.enums import Env

        mock_pickle.load.return_value = {"spec": "cached", "build_options": {}}

        with patch("app.spec.load.ENV", Env.PROD), patch("app.spec.load.Path") as mock_path_cls:
            mock_cache_file = MagicMock()
            mock_cache_file.exists.return_value = True
            mock_cache_file.open.return_value.__enter__.return_value = MagicMock()
            mock_path_cls.return_value = mock_cache_file

            result = load_spec()

        assert result == "cached"

    # ------------------------------------------------------------------
    # load_spec() — non-prod invalidation
    # ------------------------------------------------------------------

    def test_load_spec_non_prod_invalidates_on_mtime(
        self,
        mock_yaml_full_load: Any,
        mock_resolve_refs: Any,
        mock_pickle: Any,
    ) -> None:
        """Non-prod mode invalidates cache when a spec YAML file is newer."""
        from app.enums import Env

        mock_pickle.load.return_value = {
            "spec": "old_spec",
            "build_options": {"env": Env.DEV, "disable_security": False},
        }

        with (
            patch("app.spec.load.ENV", Env.DEV),
            patch(
                "app.spec.load._current_build_options",
                return_value={"env": Env.DEV, "disable_security": False},
            ),
            patch("app.spec.load._get_latest_spec_mtime", return_value=200.0),
            patch("app.spec.load.Path") as mock_path_cls,
        ):
            mock_cache_file = MagicMock()
            mock_cache_file.exists.return_value = True
            mock_cache_file.open.return_value.__enter__.return_value = MagicMock()
            mock_cache_file.stat.return_value.st_mtime = 100.0
            mock_path_cls.return_value = mock_cache_file

            with patch("app.spec.load._build_spec") as mock_build:
                mock_build.return_value = {"spec": "new_spec"}
                result = load_spec()

        assert result == {"spec": "new_spec"}
        mock_build.assert_called_once()

    def test_load_spec_non_prod_invalidates_on_options(
        self,
        mock_yaml_full_load: Any,
        mock_resolve_refs: Any,
        mock_pickle: Any,
    ) -> None:
        """Non-prod mode invalidates cache when build options differ."""
        from app.enums import Env

        mock_pickle.load.return_value = {
            "spec": "old_spec",
            "build_options": {"env": Env.DEV, "disable_security": False},
        }

        with (
            patch("app.spec.load.ENV", Env.DEV),
            patch(
                "app.spec.load._current_build_options",
                return_value={"env": Env.DEV, "disable_security": True},
            ),
            patch("app.spec.load._get_latest_spec_mtime", return_value=90.0),
            patch("app.spec.load.Path") as mock_path_cls,
        ):
            mock_cache_file = MagicMock()
            mock_cache_file.exists.return_value = True
            mock_cache_file.open.return_value.__enter__.return_value = MagicMock()
            mock_cache_file.stat.return_value.st_mtime = 200.0
            mock_path_cls.return_value = mock_cache_file

            with patch("app.spec.load._build_spec") as mock_build:
                mock_build.return_value = {"spec": "new_spec"}
                result = load_spec()

        assert result == {"spec": "new_spec"}
        mock_build.assert_called_once()

    # ------------------------------------------------------------------
    # load_spec() — corrupt cache handling
    # ------------------------------------------------------------------

    def test_load_spec_corrupt_cache_rebuilds(
        self, mock_yaml_full_load: Any, mock_resolve_refs: Any, mock_pickle: Any
    ) -> None:
        """A corrupt cache (EOFError) triggers a rebuild."""
        mock_pickle.load.side_effect = EOFError

        with patch("app.spec.load.Path") as mock_path_cls:
            mock_cache_file = MagicMock()
            mock_cache_file.exists.return_value = True
            mock_cache_file.open.return_value.__enter__.return_value = MagicMock()
            mock_path_cls.return_value = mock_cache_file

            with patch("app.spec.load._build_spec") as mock_build:
                mock_build.return_value = {"spec": "rebuilt"}
                result = load_spec()

        assert result == {"spec": "rebuilt"}
        mock_build.assert_called_once()

    def test_load_spec_corrupt_cache_unpickling_error_rebuilds(
        self, mock_yaml_full_load: Any, mock_resolve_refs: Any, mock_pickle: Any
    ) -> None:
        """A corrupt cache (UnpicklingError) triggers a rebuild."""
        mock_pickle.load.side_effect = pickle.UnpicklingError("bad data")

        with patch("app.spec.load.Path") as mock_path_cls:
            mock_cache_file = MagicMock()
            mock_cache_file.exists.return_value = True
            mock_cache_file.open.return_value.__enter__.return_value = MagicMock()
            mock_path_cls.return_value = mock_cache_file

            with patch("app.spec.load._build_spec") as mock_build:
                mock_build.return_value = {"spec": "rebuilt"}
                result = load_spec()

        assert result == {"spec": "rebuilt"}
        mock_build.assert_called_once()

    # ------------------------------------------------------------------
    # _build_spec()
    # ------------------------------------------------------------------

    def test_build_spec_loads_yaml(self, mock_yaml_full_load: Any, mock_resolve_refs: Any) -> None:
        """_build_spec loads the entrypoint YAML."""
        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}

        with patch("app.spec.load.Path") as mock_path_cls:
            mock_entrypoint = MagicMock()
            mock_entrypoint.open.return_value.__enter__.return_value = MagicMock()
            mock_cache = MagicMock()
            mock_cache.open.return_value.__enter__.return_value = MagicMock()
            mock_path_cls.side_effect = [mock_entrypoint, mock_cache]

            with (
                patch("app.spec.load._current_build_options", return_value={}),
                patch("app.spec.load.pickle.dump"),
            ):
                result = _build_spec()

        assert "components" in result
        mock_yaml_full_load.assert_called_once()

    def test_build_spec_resolves_refs(
        self, mock_yaml_full_load: Any, mock_resolve_refs: Any
    ) -> None:
        """_build_spec resolves $ref references."""
        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {"resolved": True}}}

        with patch("app.spec.load.Path") as mock_path_cls:
            mock_entrypoint = MagicMock()
            mock_entrypoint.open.return_value.__enter__.return_value = MagicMock()
            mock_cache = MagicMock()
            mock_cache.open.return_value.__enter__.return_value = MagicMock()
            mock_path_cls.side_effect = [mock_entrypoint, mock_cache]

            with (
                patch("app.spec.load._current_build_options", return_value={}),
                patch("app.spec.load.pickle.dump"),
            ):
                result = _build_spec()

        assert result == {"components": {"schemas": {"resolved": True}}}
        mock_resolve_refs.assert_called_once()

    def test_build_spec_applies_mutations(
        self, mock_yaml_full_load: Any, mock_resolve_refs: Any
    ) -> None:
        """_build_spec applies post-processing mutations."""
        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}

        with patch("app.spec.load.Path") as mock_path_cls:
            mock_entrypoint = MagicMock()
            mock_entrypoint.open.return_value.__enter__.return_value = MagicMock()
            mock_cache = MagicMock()
            mock_cache.open.return_value.__enter__.return_value = MagicMock()
            mock_path_cls.side_effect = [mock_entrypoint, mock_cache]

            with (
                patch("app.spec.load._current_build_options", return_value={}),
                patch("app.spec.load.pickle.dump"),
                patch("app.spec.load.populate_shallow_refs") as mock_populate,
            ):
                _build_spec()

        mock_populate.assert_called_once()

    def test_build_spec_writes_cache(
        self, mock_yaml_full_load: Any, mock_resolve_refs: Any, mock_pickle: Any
    ) -> None:
        """_build_spec writes the cache file via pickle.dump."""
        mock_yaml_full_load.return_value = {"components": {"schemas": {}}}
        mock_resolve_refs.return_value = {"components": {"schemas": {}}}
        mock_pickle.dump.return_value = None

        with patch("app.spec.load.Path") as mock_path_cls:
            mock_entrypoint = MagicMock()
            mock_entrypoint.open.return_value.__enter__.return_value = MagicMock()
            mock_cache = MagicMock()
            mock_cache.open.return_value.__enter__.return_value = MagicMock()
            mock_path_cls.side_effect = [mock_entrypoint, mock_cache]

            with (
                patch("app.spec.load._current_build_options", return_value={}),
                patch("app.spec.load.pickle.dump") as mock_dump,
            ):
                _build_spec()

        assert mock_dump.called

    # ------------------------------------------------------------------
    # _apply_mutations()
    # ------------------------------------------------------------------

    def test_apply_mutations_populates_shallow_refs(self) -> None:
        """_apply_mutations calls populate_shallow_refs."""
        spec: dict[str, Any] = {"components": {"schemas": {}}}

        with patch("app.spec.load.populate_shallow_refs") as mock_populate:
            _apply_mutations(spec)

        mock_populate.assert_called_once_with(spec)

    def test_apply_mutations_removes_security_when_disabled(self) -> None:
        """Security requirements are removed when security is disabled in non-prod."""
        from app.enums import Env

        spec = {
            "components": {"schemas": {}},
            "security": [{"oauth": []}],
            "paths": {"/test": {"get": {"security": [{"oauth": []}]}}},
        }

        with (
            patch("app.spec.load.populate_shallow_refs"),
            patch("app.spec.load.get_security_enabled", return_value=False),
            patch("app.spec.load.ENV", Env.DEV),
        ):
            _apply_mutations(spec)

        assert "security" not in spec
        paths_get = spec["paths"]["/test"]["get"]  # type: ignore[index]
        assert "security" not in paths_get

    def test_apply_mutations_keeps_security_when_enabled(self) -> None:
        """Security requirements are kept when security is enabled."""
        from app.enums import Env

        spec: dict[str, Any] = {
            "components": {"schemas": {}},
            "security": [{"oauth": []}],
            "paths": {"/test": {"get": {"security": [{"oauth": []}]}}},
        }

        with (
            patch("app.spec.load.populate_shallow_refs"),
            patch("app.spec.load.get_security_enabled", return_value=True),
            patch("app.spec.load.ENV", Env.PROD),
        ):
            _apply_mutations(spec)

        assert "security" in spec
        paths_get = spec["paths"]["/test"]["get"]
        assert "security" in paths_get

    # ------------------------------------------------------------------
    # _current_build_options()
    # ------------------------------------------------------------------

    def test_current_build_options_returns_env_and_security(self) -> None:
        """_current_build_options returns env and disable_security flag."""
        from app.enums import Env

        with (
            patch("app.spec.load.ENV", Env.DEV),
            patch("app.spec.load.get_security_enabled", return_value=False),
        ):
            result = _current_build_options()

        assert result["env"] == Env.DEV
        assert result["disable_security"] is True

    # ------------------------------------------------------------------
    # _get_latest_spec_mtime()
    # ------------------------------------------------------------------

    def test_get_latest_spec_mtime_scans_yaml_files(self, tmp_path: Path) -> None:
        """_get_latest_spec_mtime scans all YAML files in the spec dir."""
        (tmp_path / "a.yaml").write_text("spec: a")
        (tmp_path / "b.yml").write_text("spec: b")
        (tmp_path / "c.txt").write_text("not yaml")

        with patch("app.spec.load.SPEC_DIR", str(tmp_path)):
            result = _get_latest_spec_mtime()

        assert result > 0

    def test_get_latest_spec_mtime_returns_zero_when_no_files(self, tmp_path: Path) -> None:
        """_get_latest_spec_mtime returns 0.0 when no YAML files exist."""
        with patch("app.spec.load.SPEC_DIR", str(tmp_path)):
            result = _get_latest_spec_mtime()

        assert result == 0.0

    def test_get_latest_spec_mtime_scans_recursively(self, tmp_path: Path) -> None:
        """_get_latest_spec_mtime scans subdirectories recursively."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.yaml").write_text("spec: nested")

        with patch("app.spec.load.SPEC_DIR", str(tmp_path)):
            result = _get_latest_spec_mtime()

        assert result > 0

    def test_get_latest_spec_mtime_skips_non_yaml(self, tmp_path: Path) -> None:
        """_get_latest_spec_mtime ignores non-YAML files."""
        (tmp_path / "a.yaml").write_text("spec: a")
        (tmp_path / "b.json").write_text("{}")
        (tmp_path / "c.txt").write_text("text")
        (tmp_path / "d.yml").write_text("spec: d")

        with patch("app.spec.load.SPEC_DIR", str(tmp_path)):
            result = _get_latest_spec_mtime()

        assert result > 0
