"""High-level LDraw -> glTF conversion."""

import os
from pathlib import Path

from . import _native
from .gltf import write_gltf
from .library import resolve_library
from .scene import build_jobs

__all__ = ["convert", "load_scene", "DEFAULT_SCALE"]

DEFAULT_SCALE = 0.0004  # 1 LDU = 0.4 mm -> meters

_STUD_TYPES = {
    "normal": _native.StudType.Normal,
    "logo": _native.StudType.Logo4,
    "none": _native.StudType.Disabled,
    "high-contrast": _native.StudType.HighContrast,
}


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
    settings = _build_settings(scale, studs, gaps)
    return _native.load_file_instanced(str(in_path), str(library), [], settings)


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
    settings = _build_settings(scale, studs, gaps)
    scene = _native.load_file_instanced(str(in_path), str(library), [], settings)
    color_table = _native.load_color_table(str(library))
    jobs = build_jobs(scene)
    out_path = Path(out_path)
    write_gltf(jobs, color_table, out_path)
    return out_path
