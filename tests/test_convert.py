from pathlib import Path

import pygltflib
import pytest

import ldraw2mesh

pytestmark = pytest.mark.native

FIXTURES = Path(__file__).parent / "fixtures"
LIBRARY = FIXTURES / "ldraw"
MODEL = FIXTURES / "model.ldr"


def test_convert_produces_loadable_glb(tmp_path):
    out = tmp_path / "model.glb"
    result = ldraw2mesh.convert(MODEL, out, ldraw_library=LIBRARY)
    assert result == out and out.exists()

    g = pygltflib.GLTF2().load(str(out))
    assert len(g.meshes) >= 1
    assert len(g.materials) >= 1
    assert len(g.nodes) >= 2  # at least one instance + root
    assert g.scene == 0


def test_convert_writes_text_gltf(tmp_path):
    out = tmp_path / "model.gltf"
    ldraw2mesh.convert(MODEL, out, ldraw_library=LIBRARY)
    g = pygltflib.GLTF2().load(str(out))
    assert len(g.meshes) >= 1


def test_load_scene_returns_instanced_scene():
    scene = ldraw2mesh.load_scene(MODEL, ldraw_library=LIBRARY)
    assert hasattr(scene, "geometry_world_transforms")
    assert hasattr(scene, "geometry_cache")
    assert len(scene.geometry_cache) >= 1
