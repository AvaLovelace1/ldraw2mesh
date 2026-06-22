from dataclasses import dataclass

import pygltflib

from ldraw2mesh.materials import fallback_material, material_for_color


@dataclass
class FakeColor:
    name: str
    finish_name: str
    rgba_linear: tuple[float, float, float, float]


def test_opaque_solid_color():
    mat = material_for_color(FakeColor("Red", "", (0.7, 0.0, 0.0, 1.0)))
    assert mat.alphaMode == pygltflib.OPAQUE
    pbr = mat.pbrMetallicRoughness
    assert pbr is not None
    assert pbr.baseColorFactor == [0.7, 0.0, 0.0, 1.0]
    assert pbr.metallicFactor == 0.0


def test_transparent_color_uses_blend():
    mat = material_for_color(FakeColor("Trans", "Transparent", (0.0, 0.5, 0.0, 0.4)))
    assert mat.alphaMode == pygltflib.BLEND


def test_chrome_is_metallic():
    mat = material_for_color(FakeColor("Chrome", "Chrome", (0.8, 0.8, 0.8, 1.0)))
    pbr = mat.pbrMetallicRoughness
    assert pbr is not None
    assert pbr.metallicFactor == 1.0
    assert pbr.roughnessFactor is not None
    assert pbr.roughnessFactor < 0.5


def test_fallback_material_is_valid():
    mat = fallback_material(9999)
    assert isinstance(mat, pygltflib.Material)
    pbr = mat.pbrMetallicRoughness
    assert pbr is not None
    assert pbr.baseColorFactor is not None
    assert pbr.baseColorFactor[3] == 1.0
