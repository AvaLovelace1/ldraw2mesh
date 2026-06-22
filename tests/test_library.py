import pytest

from ldraw2mesh.library import LDrawLibraryNotFound, resolve_library


def _make_library(root):
    (root / "LDConfig.ldr").write_text("0 // minimal\n")
    (root / "parts").mkdir()
    return root


def test_explicit_path_wins(tmp_path, monkeypatch):
    (tmp_path / "lib").mkdir(exist_ok=True)
    lib = _make_library(tmp_path / "lib")
    monkeypatch.delenv("LDRAW_LIBRARY_PATH", raising=False)
    assert resolve_library(lib) == lib.resolve()


def test_env_var_used_when_no_explicit(tmp_path, monkeypatch):
    lib = tmp_path / "env_lib"
    lib.mkdir()
    _make_library(lib)
    monkeypatch.setenv("LDRAW_LIBRARY_PATH", str(lib))
    assert resolve_library() == lib.resolve()


def test_missing_library_raises_actionable_error(tmp_path, monkeypatch):
    monkeypatch.delenv("LDRAW_LIBRARY_PATH", raising=False)
    missing = tmp_path / "nope"
    with pytest.raises(LDrawLibraryNotFound) as exc:
        resolve_library(missing)
    assert "ldraw.org" in str(exc.value).lower()


def test_directory_without_ldconfig_or_parts_is_invalid(tmp_path, monkeypatch):
    monkeypatch.delenv("LDRAW_LIBRARY_PATH", raising=False)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(LDrawLibraryNotFound):
        resolve_library(empty)
