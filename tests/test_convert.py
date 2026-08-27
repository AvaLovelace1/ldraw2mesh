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


def test_missing_input_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ldraw2mesh.convert(
            tmp_path / "nope.ldr", tmp_path / "o.glb", ldraw_library=LIBRARY
        )


def test_directory_input_raises(tmp_path):
    with pytest.raises(IsADirectoryError):
        ldraw2mesh.convert(tmp_path, tmp_path / "o.glb", ldraw_library=LIBRARY)


def test_file_with_no_geometry_raises_instead_of_writing_empty_gltf(tmp_path):
    empty = tmp_path / "empty.ldr"
    empty.write_text("0 Just a comment, no parts\n")
    out = tmp_path / "o.glb"
    with pytest.raises(ldraw2mesh.EmptySceneError):
        ldraw2mesh.convert(empty, out, ldraw_library=LIBRARY)
    assert not out.exists()


def test_unresolvable_part_raises_instead_of_writing_empty_gltf(tmp_path):
    model = tmp_path / "missing_part.ldr"
    model.write_text("1 4 0 0 0 1 0 0 0 1 0 0 0 1 not-in-this-library.dat\n")
    out = tmp_path / "o.glb"
    with pytest.raises(ldraw2mesh.EmptySceneError):
        ldraw2mesh.convert(model, out, ldraw_library=LIBRARY)
    assert not out.exists()
