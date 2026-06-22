"""Flatten an instanced LDraw scene into per-(geometry, color) mesh build jobs."""

from dataclasses import dataclass

import numpy as np

__all__ = ["CURRENT_COLOR", "MeshJob", "build_jobs"]

CURRENT_COLOR = 16  # LDraw code meaning "use the instance's current color"


@dataclass
class MeshJob:
    path_name: str
    color: int
    positions: np.ndarray  # (V, 3) float32
    triangles: np.ndarray  # (T, 3) uint32
    face_colors: np.ndarray  # (T,) uint32, resolved (16 -> instance color)
    hard_edges: np.ndarray  # (E, 2) uint32
    transforms: np.ndarray  # (N, 4, 4) float32, row-major world transforms


def build_jobs(scene) -> list[MeshJob]:
    jobs: list[MeshJob] = []
    for (path, color), transforms in scene.geometry_world_transforms.items():
        geom = scene.geometry_cache[path]

        vidx = np.asarray(geom.vertex_indices, dtype=np.uint32)
        if vidx.size % 3 != 0:
            raise ValueError(
                f"geometry {path.normalized_name!r} is not triangulated "
                f"(vertex_indices length {vidx.size} is not a multiple of 3); "
                "set GeometrySettings.triangulate = True"
            )
        triangles = vidx.reshape(-1, 3)
        n_faces = triangles.shape[0]

        face_colors = np.asarray(geom.face_colors, dtype=np.uint32)
        # ldr_tools compresses uniform-color geometry to a single entry; expand back.
        if face_colors.size == 1 and n_faces > 1:
            face_colors = np.full(n_faces, face_colors[0], dtype=np.uint32)
        resolved = np.where(face_colors == CURRENT_COLOR, np.uint32(color), face_colors)

        jobs.append(
            MeshJob(
                path_name=path.normalized_name,
                color=int(color),
                positions=np.asarray(geom.vertices, dtype=np.float32).reshape(-1, 3),
                triangles=triangles,
                face_colors=resolved.astype(np.uint32),
                hard_edges=np.asarray(geom.edge_line_indices, dtype=np.uint32).reshape(
                    -1, 2
                ),
                transforms=np.asarray(transforms, dtype=np.float32).reshape(-1, 4, 4),
            )
        )
    return jobs
