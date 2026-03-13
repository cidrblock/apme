"""Tests for collection cache venv builder."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from apme_engine.collection_cache.venv_builder import (
    _resolve_collection_path,
    _venv_key,
    _venv_site_packages,
    build_venv,
    get_venv_python,
)


class TestVenvKey:
    """Tests for _venv_key."""

    def test_stable_for_same_inputs(self) -> None:
        """Same version and collections produce same key."""
        assert _venv_key("2.15.0", ["ansible.builtin.debug"]) == _venv_key("2.15.0", ["ansible.builtin.debug"])

    def test_different_version_different_key(self) -> None:
        """Different ansible-core versions produce different keys."""
        k1 = _venv_key("2.14.0", [])
        k2 = _venv_key("2.15.0", [])
        assert k1 != k2

    def test_different_collections_different_key(self) -> None:
        """Different collection lists produce different keys."""
        k1 = _venv_key("2.15.0", ["a.b"])
        k2 = _venv_key("2.15.0", ["a.b", "c.d"])
        assert k1 != k2

    def test_order_of_collections_irrelevant(self) -> None:
        """Collection order does not affect key."""
        k1 = _venv_key("2.15.0", ["c.d", "a.b"])
        k2 = _venv_key("2.15.0", ["a.b", "c.d"])
        assert k1 == k2


class TestVenvSitePackages:
    """Tests for _venv_site_packages."""

    def test_returns_site_packages_under_lib_python(self, tmp_path: Path) -> None:
        """Returns site-packages path under lib/pythonX.Y.

        Args:
            tmp_path: Pytest temporary directory fixture.

        """
        (tmp_path / "lib" / "python3.12" / "site-packages").mkdir(parents=True)
        assert _venv_site_packages(tmp_path) == tmp_path / "lib" / "python3.12" / "site-packages"

    def test_creates_site_packages_if_missing(self, tmp_path: Path) -> None:
        """Creates site-packages dir if lib/pythonX.Y exists.

        Args:
            tmp_path: Pytest temporary directory fixture.

        """
        (tmp_path / "lib" / "python3.11").mkdir(parents=True)
        out = _venv_site_packages(tmp_path)
        assert out.is_dir()
        assert out == tmp_path / "lib" / "python3.11" / "site-packages"

    def test_no_lib_raises(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError when no lib dir.

        Args:
            tmp_path: Pytest temporary directory fixture.

        """
        with pytest.raises(FileNotFoundError, match="no lib dir"):
            _venv_site_packages(tmp_path)


class TestResolveCollectionPath:
    """Tests for _resolve_collection_path."""

    def test_returns_none_when_not_in_cache(self, tmp_path: Path) -> None:
        """Returns None when collection not in cache.

        Args:
            tmp_path: Pytest temporary directory fixture.

        """
        assert _resolve_collection_path("namespace.collection", tmp_path) is None

    def test_returns_path_when_in_galaxy_cache(self, tmp_path: Path) -> None:
        """Returns path when collection exists in galaxy cache.

        Args:
            tmp_path: Pytest temporary directory fixture.

        """
        ac = tmp_path / "galaxy" / "ansible_collections" / "ns" / "coll"
        ac.mkdir(parents=True)
        path = _resolve_collection_path("ns.coll", tmp_path)
        assert path == ac


class TestGetVenvPython:
    """Tests for get_venv_python."""

    def test_returns_bin_python_on_unix(self, tmp_path: Path) -> None:
        """Returns bin/python on Unix.

        Args:
            tmp_path: Pytest temporary directory fixture.

        """
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        (bin_dir / "python").touch()
        assert get_venv_python(tmp_path) == tmp_path / "bin" / "python"

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")  # type: ignore[untyped-decorator]
    def test_returns_scripts_python_on_windows(self, tmp_path: Path) -> None:
        """Returns Scripts/python.exe on Windows.

        Args:
            tmp_path: Pytest temporary directory fixture.

        """
        scripts = tmp_path / "Scripts"
        scripts.mkdir()
        (scripts / "python.exe").touch()
        assert get_venv_python(tmp_path) == tmp_path / "Scripts" / "python.exe"


class TestBuildVenv:
    """Tests for build_venv."""

    def test_missing_collection_raises(self, tmp_path: Path) -> None:
        """When a collection spec is not in cache, build_venv raises FileNotFoundError.

        Args:
            tmp_path: Pytest temporary directory fixture.

        """
        base = tmp_path / "v"
        base.mkdir()

        def run_side_effect(*args: object, **kwargs: object) -> object:
            cmd = list(args[0]) if args else list(kwargs.get("args", []))  # type: ignore[call-overload]
            if not cmd:
                return MagicMock(returncode=0)
            # First run: venv create (uv venv <path> or python -m venv <path>)
            if "venv" in str(cmd) or (len(cmd) >= 2 and cmd[1] == "-m" and cmd[2] == "venv"):
                venv_path = Path(cmd[-1])
                venv_path.mkdir(parents=True)
                (venv_path / "lib" / "python3.12" / "site-packages").mkdir(parents=True)
                (venv_path / "pyvenv.cfg").write_text("[venv]")
            return MagicMock(returncode=0)

        with (
            patch("subprocess.run", side_effect=run_side_effect),
            pytest.raises(FileNotFoundError, match="Collection not in cache"),
        ):
            build_venv(
                "2.15.0",
                ["ns.missing"],
                cache_root=tmp_path,
                venvs_root=base,
            )

    @pytest.mark.integration  # type: ignore[untyped-decorator]
    def test_build_venv_empty_collections(self, tmp_path: Path) -> None:
        """With no collections, build_venv creates venv with ansible-core only (needs network).

        Args:
            tmp_path: Pytest temporary directory fixture.

        """
        venv_root = build_venv(
            "2.15.0",
            [],
            cache_root=tmp_path,
            venvs_root=tmp_path / "venvs",
        )
        assert venv_root.is_dir()
        assert (venv_root / "pyvenv.cfg").is_file()
        py = get_venv_python(venv_root)
        assert py.is_file()
        ac = _venv_site_packages(venv_root) / "ansible_collections"
        assert ac.is_dir()
