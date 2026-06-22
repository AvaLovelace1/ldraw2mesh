"""Assemble glTF (.glb/.gltf) from mesh build jobs using pygltflib."""

import base64
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pygltflib

from .materials import fallback_material, material_for_color
from .normals import edge_aware_normals
from .scene import MeshJob
from .transform import LDRAW_TO_GLTF, to_gltf_matrix

__all__ = ["write_gltf"]


class _Buffer:
    """Accumulates binary data and creates aligned bufferViews."""

    def __init__(self) -> None:
        self.blob = bytearray()
        self.views: list[pygltflib.BufferView] = []

    def add(self, data: bytes, target: int) -> int:
        while len(self.blob) % 4 != 0:  # 4-byte alignment for f32/u32
            self.blob.append(0)
        offset = len(self.blob)
        self.blob.extend(data)
        self.views.append(
            pygltflib.BufferView(
                buffer=0, byteOffset=offset, byteLength=len(data), target=target
            )
        )
        return len(self.views) - 1


def write_gltf(
    jobs: list[MeshJob],
    color_table: Mapping[int, Any],
    out: str | os.PathLike[str],
) -> None:
    gltf = pygltflib.GLTF2()
    buf = _Buffer()
    material_index: dict[int, int] = {}

    def material_for(code: int) -> int:
        if code not in material_index:
            color = color_table.get(code)
            mat = (
                material_for_color(color)
                if color is not None
                else fallback_material(code)
            )
            material_index[code] = len(gltf.materials)
            gltf.materials.append(mat)
        return material_index[code]

    instance_node_indices: list[int] = []

    for job in jobs:
        positions, normals, triangles = edge_aware_normals(
            job.positions, job.triangles, job.hard_edges
        )

        pos_view = buf.add(
            positions.astype(np.float32).tobytes(), pygltflib.ARRAY_BUFFER
        )
        pos_accessor = len(gltf.accessors)
        gltf.accessors.append(
            pygltflib.Accessor(
                bufferView=pos_view,
                componentType=pygltflib.FLOAT,
                count=int(positions.shape[0]),
                type=pygltflib.VEC3,
                min=positions.min(axis=0).tolist(),
                max=positions.max(axis=0).tolist(),
            )
        )
        nrm_view = buf.add(normals.astype(np.float32).tobytes(), pygltflib.ARRAY_BUFFER)
        nrm_accessor = len(gltf.accessors)
        gltf.accessors.append(
            pygltflib.Accessor(
                bufferView=nrm_view,
                componentType=pygltflib.FLOAT,
                count=int(normals.shape[0]),
                type=pygltflib.VEC3,
            )
        )

        primitives: list[pygltflib.Primitive] = []
        for code in np.unique(job.face_colors):
            mask = job.face_colors == code
            indices = triangles[mask].reshape(-1).astype(np.uint32)
            idx_view = buf.add(indices.tobytes(), pygltflib.ELEMENT_ARRAY_BUFFER)
            idx_accessor = len(gltf.accessors)
            gltf.accessors.append(
                pygltflib.Accessor(
                    bufferView=idx_view,
                    componentType=pygltflib.UNSIGNED_INT,
                    count=int(indices.shape[0]),
                    type=pygltflib.SCALAR,
                )
            )
            primitives.append(
                pygltflib.Primitive(
                    attributes=pygltflib.Attributes(
                        POSITION=pos_accessor, NORMAL=nrm_accessor
                    ),
                    indices=idx_accessor,
                    material=material_for(int(code)),
                )
            )

        mesh_index = len(gltf.meshes)
        gltf.meshes.append(pygltflib.Mesh(name=job.path_name, primitives=primitives))

        for transform in job.transforms:
            node_index = len(gltf.nodes)
            gltf.nodes.append(
                pygltflib.Node(mesh=mesh_index, matrix=to_gltf_matrix(transform))
            )
            instance_node_indices.append(node_index)

    root_index = len(gltf.nodes)
    gltf.nodes.append(
        pygltflib.Node(
            matrix=to_gltf_matrix(LDRAW_TO_GLTF), children=instance_node_indices
        )
    )
    gltf.scenes.append(pygltflib.Scene(nodes=[root_index]))
    gltf.scene = 0

    blob = bytes(buf.blob)
    gltf.bufferViews = buf.views
    gltf.buffers = [pygltflib.Buffer(byteLength=len(blob))]

    out_path = Path(out)
    if out_path.suffix.lower() == ".glb":
        gltf.set_binary_blob(blob)
        gltf.save_binary(str(out_path))
    else:
        gltf.buffers[0].uri = (
            "data:application/octet-stream;base64,"
            + base64.b64encode(blob).decode("ascii")
        )
        gltf.save_json(str(out_path))
