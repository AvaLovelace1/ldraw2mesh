"""High-level LDraw -> glTF conversion."""

import errno
import os
from pathlib import Path

from . import _native
from .gltf import write_gltf
from .library import resolve_library
from .scene import build_jobs

__all__ = ["DEFAULT_SCALE", "EmptySceneError", "convert", "load_scene"]

DEFAULT_SCALE = 0.0004  # 1 LDU = 0.4 mm -> meters


class EmptySceneError(RuntimeError):
    """Raised when an LDraw file yields no renderable geometry."""


_STUD_TYPES = {
    "normal": _native.StudType.Normal,
    "logo": _native.StudType.Logo4,
    "none": _native.StudType.Disabled,
    "high-contrast": _native.StudType.HighContrast,
}


def _check_input(in_path: str | os.PathLike[str]) -> str:
    """Return ``in_path`` as a string, raising if it is not a readable file."""
    path = Path(in_path)
    if path.is_dir():
        raise IsADirectoryError(errno.EISDIR, "not an LDraw file", str(path))
    if not path.is_file():
        raise FileNotFoundError(errno.ENOENT, "no such LDraw file", str(path))
    return str(path)


def _build_settings(scale: float, studs: str, gaps: bool) -> _native.GeometrySettings:
    try:
        stud_type = _STUD_TYPES[studs]
    except KeyError:
        raise ValueError(
            f"unknown studs option {studs!r}; choose from {sorted(_STUD_TYPES)}"
        ) from None
    settings = _native.GeometrySettings()
    settings.triangulate = True
    settings.weld_vertices = True
    settings.scene_scale = float(scale)
    settings.stud_type = stud_type
    settings.add_gap_between_parts = bool(gaps)
    return settings


def load_scene(
    in_path: str | os.PathLike[str],
    *,
    ldraw_library: str | os.PathLike[str] | None = None,
    scale: float = DEFAULT_SCALE,
    studs: str = "normal",
    gaps: bool = False,
) -> _native.LDrawSceneInstanced:
    library = resolve_library(ldraw_library)
    source = _check_input(in_path)
    settings = _build_settings(scale, studs, gaps)
    return _native.load_file_instanced(source, str(library), [], settings)


def convert(
    in_path: str | os.PathLike[str],
    out_path: str | os.PathLike[str],
    *,
    ldraw_library: str | os.PathLike[str] | None = None,
    scale: float = DEFAULT_SCALE,
    studs: str = "normal",
    gaps: bool = False,
) -> Path:
    library = resolve_library(ldraw_library)
    source = _check_input(in_path)
    settings = _build_settings(scale, studs, gaps)
    scene = _native.load_file_instanced(source, str(library), [], settings)
    color_table = _native.load_color_table(str(library))
    jobs = build_jobs(scene)
    if not any(job.triangles.shape[0] for job in jobs):
        raise EmptySceneError(
            f"{source} produced no geometry. The file may be empty or malformed, "
            f"or its parts may be missing from the LDraw library at {library}."
        )
    out_path = Path(out_path)
    write_gltf(jobs, color_table, out_path)
    return out_path
