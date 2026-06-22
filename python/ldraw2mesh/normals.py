"""Edge-aware vertex normals.

LDraw geometry arrives as welded triangles plus a list of "hard edges" (the LDraw
edge/condition lines). We want smooth shading across soft regions but crisp seams
at hard edges. For each original vertex we union its incident triangles that share
a non-hard edge, then emit one averaged normal per resulting smoothing group,
duplicating the vertex across groups. Triangle order is preserved so per-triangle
attributes (e.g. face colors) stay aligned.
"""

from collections import defaultdict
from collections.abc import Iterable

import numpy as np

__all__ = ["face_normals", "edge_aware_normals"]


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return np.divide(v, n, out=np.zeros_like(v), where=n > 0.0)


def face_normals(positions: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    p = np.asarray(positions, dtype=np.float32)[np.asarray(triangles, dtype=np.int64)]
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    return _normalize(n).astype(np.float32)


class _UnionFind:
    def __init__(self, items: Iterable[int]) -> None:
        self.parent = {i: i for i in items}

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def edge_aware_normals(
    positions: np.ndarray,
    triangles: np.ndarray,
    hard_edges: Iterable[tuple[int, int]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    positions = np.asarray(positions, dtype=np.float32)
    triangles = np.asarray(triangles, dtype=np.int64).reshape(-1, 3)
    p = positions[triangles]
    raw_normals = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])  # magnitude ∝ area
    hard = {frozenset((int(a), int(b))) for a, b in hard_edges}

    incident: dict[int, list[int]] = defaultdict(list)
    for t, tri in enumerate(triangles):
        for v in tri:
            incident[int(v)].append(t)

    out_positions: list[np.ndarray] = []
    out_normals: list[np.ndarray] = []
    corner_index: dict[tuple[int, int], int] = {}

    for v, tris in incident.items():
        uf = _UnionFind(tris)
        edge_tris: dict[int, list[int]] = defaultdict(list)
        for t in tris:
            for w in triangles[t]:
                w = int(w)
                if w != v:
                    edge_tris[w].append(t)
        for w, ts in edge_tris.items():
            if frozenset((v, w)) in hard:
                continue
            for u in ts[1:]:
                uf.union(ts[0], u)

        groups: dict[int, list[int]] = defaultdict(list)
        for t in tris:
            groups[uf.find(t)].append(t)
        for gts in groups.values():
            normal = _normalize(raw_normals[gts].sum(axis=0))
            idx = len(out_positions)
            out_positions.append(positions[v])
            out_normals.append(normal)
            for t in gts:
                corner_index[(v, t)] = idx

    out_triangles = np.array(
        [
            [corner_index[(int(v), t)] for v in triangles[t]]
            for t in range(len(triangles))
        ],
        dtype=np.uint32,
    )
    return (
        np.asarray(out_positions, dtype=np.float32).reshape(-1, 3),
        np.asarray(out_normals, dtype=np.float32).reshape(-1, 3),
        out_triangles,
    )
