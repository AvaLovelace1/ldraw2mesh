from dataclasses import dataclass

import numpy as np
import pygltflib

from ldraw2mesh.gltf import write_gltf
from ldraw2mesh.scene import MeshJob


@dataclass
class FakeColor:
    name: str
    finish_name: str
    rgba_linear: tuple[float, float, float, float]


def _one_quad_job(n_instances=3):
    return MeshJob(
        path_name="tri.dat",
        color=4,
        positions=np.array(
            [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=np.float32
        ),
        triangles=np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32),
        face_colors=np.array([4, 4], dtype=np.uint32),
        hard_edges=np.empty((0, 2), dtype=np.uint32),
        transforms=np.stack([np.eye(4, dtype=np.float32)] * n_instances),
    )


def _color_table():
    return {4: FakeColor("Red", "", (0.7, 0.0, 0.0, 1.0))}


def test_writes_loadable_glb(tmp_path):
    out = tmp_path / "out.glb"
    write_gltf([_one_quad_job()], _color_table(), out)
    g = pygltflib.GLTF2().load(str(out))
    assert len(g.meshes) == 1
    assert len(g.materials) == 1
    # 3 instance nodes + 1 root
    assert len(g.nodes) == 4
    assert len(g.scenes[0].nodes) == 1  # single root


def test_writes_loadable_gltf_text(tmp_path):
    out = tmp_path / "out.gltf"
    write_gltf([_one_quad_job(1)], _color_table(), out)
    g = pygltflib.GLTF2().load(str(out))
    assert len(g.meshes) == 1
    assert g.buffers[0].uri is not None and g.buffers[0].uri.startswith("data:")


def test_two_colors_make_two_primitives(tmp_path):
    job = _one_quad_job(1)
    job.face_colors = np.array([4, 7], dtype=np.uint32)
    table = {
        4: FakeColor("Red", "", (0.7, 0, 0, 1.0)),
        7: FakeColor("Gray", "", (0.5, 0.5, 0.5, 1.0)),
    }
    out = tmp_path / "two.glb"
    write_gltf([job], table, out)
    g = pygltflib.GLTF2().load(str(out))
    assert len(g.meshes[0].primitives) == 2
    assert len(g.materials) == 2


def test_unknown_color_uses_fallback(tmp_path):
    job = _one_quad_job(1)
    out = tmp_path / "fallback.glb"
    write_gltf([job], {}, out)  # empty color table
    g = pygltflib.GLTF2().load(str(out))
    assert len(g.materials) == 1  # fallback created
