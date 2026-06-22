"""Coordinate-system conversion between LDraw and glTF.

LDraw is right-handed with +Y pointing DOWN; glTF is right-handed with +Y UP.
Native transform arrays are row-major (world = M @ local_column_vector); glTF node
matrices are column-major, so we transpose-then-flatten.
"""

import numpy as np

__all__ = ["LDRAW_TO_GLTF", "to_gltf_matrix"]

LDRAW_TO_GLTF: np.ndarray = np.diag([1.0, -1.0, -1.0, 1.0]).astype(np.float32)


def to_gltf_matrix(m: np.ndarray) -> list[float]:
    """Convert a row-major 4x4 matrix to a glTF column-major length-16 float list."""
    arr = np.asarray(m, dtype=np.float32).reshape(4, 4)
    return arr.T.reshape(-1).tolist()
