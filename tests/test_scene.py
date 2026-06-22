from dataclasses import dataclass

import numpy as np

from ldraw2mesh.scene import CURRENT_COLOR, build_jobs


@dataclass(frozen=True)
class FakePath:
    normalized_name: str


@dataclass
class FakeGeometry:
    vertices: np.ndarray
    vertex_indices: np.ndarray
    face_sizes: np.ndarray
    face_colors: np.ndarray
    edge_line_indices: np.ndarray


class FakeScene:
    def __init__(self, geometry_world_transforms, geometry_cache):
        self.geometry_world_transforms = geometry_world_transforms
        self.geometry_cache = geometry_cache


def _quad_geometry(face_colors):
    return FakeGeometry(
        vertices=np.array(
            [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=np.float32
        ),
        vertex_indices=np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32),
        face_sizes=np.array([3, 3], dtype=np.uint32),
        face_colors=np.array(face_colors, dtype=np.uint32),
        edge_line_indices=np.array([[0, 1]], dtype=np.uint32),
    )


def test_build_jobs_resolves_current_color():
    path = FakePath("tri.dat")
    geom = _quad_geometry([CURRENT_COLOR, 4])
    transforms = np.stack([np.eye(4, dtype=np.float32)] * 2)
    scene = FakeScene({(path, 4): transforms}, {path: geom})

    jobs = build_jobs(scene)
    assert len(jobs) == 1
    job = jobs[0]
    assert job.color == 4
    assert job.path_name == "tri.dat"
    assert job.triangles.shape == (2, 3)
    assert job.face_colors.tolist() == [4, 4]  # 16 -> instance color 4
    assert job.transforms.shape == (2, 4, 4)


def test_build_jobs_rejects_non_triangulated():
    import pytest

    path = FakePath("bad.dat")
    geom = _quad_geometry([4])
    geom.vertex_indices = np.array(
        [0, 1, 2, 3], dtype=np.uint32
    )  # 4, not multiple of 3
    scene = FakeScene(
        {(path, 4): np.stack([np.eye(4, dtype=np.float32)])}, {path: geom}
    )
    with pytest.raises(ValueError):
        build_jobs(scene)


def test_build_jobs_broadcasts_uniform_color():
    """ldr_tools may compress uniform face_colors to a single element; build_jobs broadcasts it."""
    path = FakePath("tri.dat")
    geom = _quad_geometry([4])  # length-1 but the geometry has 2 triangles
    scene = FakeScene(
        {(path, 7): np.stack([np.eye(4, dtype=np.float32)])}, {path: geom}
    )
    jobs = build_jobs(scene)
    assert jobs[0].face_colors.tolist() == [4, 4]


def test_build_jobs_broadcasts_current_color_uniform():
    """A compressed single entry equal to 16 broadcasts, then resolves to the instance color."""
    path = FakePath("tri.dat")
    geom = _quad_geometry([CURRENT_COLOR])
    scene = FakeScene(
        {(path, 9): np.stack([np.eye(4, dtype=np.float32)])}, {path: geom}
    )
    jobs = build_jobs(scene)
    assert jobs[0].face_colors.tolist() == [9, 9]
