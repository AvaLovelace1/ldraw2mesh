"""Map LDraw colors to glTF PBR metallic-roughness materials."""

from collections.abc import Sequence
from typing import Protocol

import pygltflib

__all__ = ["FALLBACK_RGBA", "fallback_material", "material_for_color"]

FALLBACK_RGBA: tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0)


class _Color(Protocol):
    """Read-only view of the fields ``_native.LDrawColor`` exposes."""

    @property
    def name(self) -> str: ...
    @property
    def finish_name(self) -> str: ...
    @property
    def rgba_linear(self) -> Sequence[float]: ...


def _pbr(
    rgba: Sequence[float], metallic: float, roughness: float
) -> pygltflib.PbrMetallicRoughness:
    r, g, b, a = (float(x) for x in rgba)
    return pygltflib.PbrMetallicRoughness(
        baseColorFactor=[r, g, b, a],
        metallicFactor=metallic,
        roughnessFactor=roughness,
    )


def material_for_color(color: _Color) -> pygltflib.Material:
    rgba = color.rgba_linear
    finish = (color.finish_name or "").lower()

    metallic, roughness = 0.0, 0.5
    if "chrome" in finish:
        metallic, roughness = 1.0, 0.2
    elif "metal" in finish:
        metallic, roughness = 0.8, 0.25
    elif "pearl" in finish:
        metallic, roughness = 0.6, 0.35
    elif "rubber" in finish:
        roughness = 0.9

    transparent = float(rgba[3]) < 1.0 or "transparent" in finish
    return pygltflib.Material(
        name=color.name or None,
        pbrMetallicRoughness=_pbr(rgba, metallic, roughness),
        alphaMode=pygltflib.BLEND if transparent else pygltflib.OPAQUE,
        doubleSided=False,
    )


def fallback_material(code: int) -> pygltflib.Material:
    return pygltflib.Material(
        name=f"ldraw_color_{code}",
        pbrMetallicRoughness=_pbr(FALLBACK_RGBA, 0.0, 0.5),
        alphaMode=pygltflib.OPAQUE,
        doubleSided=False,
    )
