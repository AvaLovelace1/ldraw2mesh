"""Locate an on-disk LDraw parts library."""

import os
import sys
from pathlib import Path

__all__ = ["LDrawLibraryNotFound", "resolve_library"]


class LDrawLibraryNotFound(Exception):
    """Raised when no LDraw parts library can be located."""


def _is_library(path: Path) -> bool:
    return path.is_dir() and (
        (path / "LDConfig.ldr").is_file() or (path / "parts").is_dir()
    )


def _candidates() -> list[Path]:
    home = Path.home()
    paths = [home / "ldraw", Path("/usr/share/ldraw"), Path("/usr/local/share/ldraw")]
    if sys.platform == "darwin":
        paths.append(home / "Library" / "ldraw")
    elif sys.platform == "win32":
        paths.append(Path("C:/LDraw"))
        paths.append(Path("C:/Program Files/LDraw"))
    return paths


def resolve_library(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Return the path to an LDraw parts library, or raise ``LDrawLibraryNotFound``."""
    searched: list[Path] = []

    if explicit is not None:
        path = Path(explicit).expanduser()
        searched.append(path)
        if _is_library(path):
            return path.resolve()

    env = os.environ.get("LDRAW_LIBRARY_PATH")
    if env:
        path = Path(env).expanduser()
        searched.append(path)
        if _is_library(path):
            return path.resolve()

    for path in _candidates():
        searched.append(path)
        if _is_library(path):
            return path.resolve()

    tried = "\n  ".join(str(p) for p in searched) or "(none)"
    raise LDrawLibraryNotFound(
        "Could not find an LDraw parts library. Download the official library from "
        "https://www.ldraw.org/ , then pass its path via --ldraw-library or set "
        "$LDRAW_LIBRARY_PATH.\nSearched:\n  " + tried
    )
