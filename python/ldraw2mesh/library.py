"""Locate an on-disk LDraw parts library."""

import os
import sys
from pathlib import Path

__all__ = ["LDrawLibraryNotFound", "resolve_library"]

_DOWNLOAD_HINT = (
    "Download the official library from https://www.ldraw.org/ , then pass its path "
    "via --ldraw-library or set $LDRAW_LIBRARY_PATH."
)


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


def _require(path: Path, source: str) -> Path:
    """Return ``path`` if it is a library, else raise naming where it came from."""
    if _is_library(path):
        return path.resolve()
    reason = (
        "is not a directory" if not path.is_dir() else "has no LDConfig.ldr or parts/"
    )
    raise LDrawLibraryNotFound(
        f"{source} points at {path}, which {reason}, so it is not an LDraw parts "
        f"library. {_DOWNLOAD_HINT}"
    )


def resolve_library(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Return the path to an LDraw parts library, or raise ``LDrawLibraryNotFound``."""
    if explicit is not None:
        return _require(Path(explicit).expanduser(), "The requested LDraw library")

    env = os.environ.get("LDRAW_LIBRARY_PATH")
    if env:
        return _require(Path(env).expanduser(), "$LDRAW_LIBRARY_PATH")

    searched: list[Path] = []
    for path in _candidates():
        searched.append(path)
        if _is_library(path):
            return path.resolve()

    tried = "\n  ".join(str(p) for p in searched) or "(none)"
    raise LDrawLibraryNotFound(
        f"Could not find an LDraw parts library. {_DOWNLOAD_HINT}\nSearched:\n  "
        + tried
    )
