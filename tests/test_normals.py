import numpy as np

from ldraw2mesh.normals import edge_aware_normals, face_normals


def test_face_normals_unit_and_oriented():
    pos = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32)
    tris = np.array([[0, 1, 2]], dtype=np.uint32)
    n = face_normals(pos, tris)
    assert np.allclose(n[0], [0, 0, 1])


def test_smooth_bend_without_hard_edge_averages_normals():
    # Two triangles sharing edge (0,1), bent along it, no hard edge -> shared
    # verts get one (averaged) normal; output has 4 vertices.
    pos = np.array([[0, 0, 0], [1, 0, 0], [0.5, 1, 0], [0.5, -1, 1]], dtype=np.float32)
    tris = np.array([[0, 1, 2], [1, 0, 3]], dtype=np.uint32)
    out_pos, out_norm, out_tris = edge_aware_normals(pos, tris, hard_edges=[])
    assert out_pos.shape[0] == 4  # nothing split
    assert np.allclose(np.linalg.norm(out_norm, axis=1), 1.0)


def test_hard_edge_splits_seam():
    # Same geometry, but mark (0,1) hard -> the two shared verts each split in
    # two, one per face: 6 output vertices, each carrying its own face normal.
    pos = np.array([[0, 0, 0], [1, 0, 0], [0.5, 1, 0], [0.5, -1, 1]], dtype=np.float32)
    tris = np.array([[0, 1, 2], [1, 0, 3]], dtype=np.uint32)
    out_pos, out_norm, out_tris = edge_aware_normals(pos, tris, hard_edges=[(0, 1)])
    assert out_pos.shape[0] == 6
    assert out_tris.shape == (2, 3)
    # the two triangles now reference disjoint vertex sets
    assert set(out_tris[0].tolist()).isdisjoint(out_tris[1].tolist())


def test_area_weighted_blended_normal():
    # Two flat triangles sharing edge (0,1) with no hard edge.
    # Triangle A (large, ~4x area): lies in XY-plane, normal = +Z.
    # Triangle B (small): tilted 90° toward XZ-plane, normal = +Y.
    # Shared vertices 0 and 1 must get area-weighted blend, NOT unit-average.
    #
    # A: (0,0,0), (4,0,0), (0,0,1)  — base=4, height=1, area=2
    # B: (0,0,0), (4,0,0), (0,1,0)  — base=4, height=1, area=2  <- this keeps same area
    #
    # Use different areas: make A have area 4x larger than B.
    # A: (0,0,0), (4,0,0), (0,4,0)  area = 8  normal = +Z  (XY plane)
    # B: (0,0,0), (4,0,0), (0,0,1)  area = 2  normal = +Y  (XZ plane, winding gives +Y or -Y)
    # raw cross for A: (4,0,0)×(0,4,0) = (0*0-0*4, 0*0-4*0, 4*4-0*0) = (0,0,16)
    # raw cross for B: (4,0,0)×(0,0,1) = (0*1-0*0, 0*0-4*1, 4*0-0*0) = (0,-4,0)
    # area-weighted sum at shared vertex: (0,0,16) + (0,-4,0) = (0,-4,16)
    # normalized: (0, -4, 16) / |(0,-4,16)|
    # unit-average: normalize((0,0,1) + (0,-1,0)) = normalize((0,-1,1))

    pos = np.array(
        [[0, 0, 0], [4, 0, 0], [0, 4, 0], [0, 0, 1]],
        dtype=np.float32,
    )
    # tri 0: A = verts 0,1,2 (large, XY-plane)
    # tri 1: B = verts 0,1,3 (small, XZ-plane)
    tris = np.array([[0, 1, 2], [0, 1, 3]], dtype=np.uint32)

    out_pos, out_norm, out_tris = edge_aware_normals(pos, tris, hard_edges=[])

    # Find the output index for vertex 0 (shared by both triangles, in one group).
    # out_tris[0][0] is the corner for vertex 0 in triangle 0.
    v0_idx = int(out_tris[0, 0])

    blended = out_norm[v0_idx]

    # Expected area-weighted normal: normalize(raw_A + raw_B)
    raw_a = np.array([0.0, 0.0, 16.0])  # cross((4,0,0),(0,4,0))
    raw_b = np.array([0.0, -4.0, 0.0])  # cross((4,0,0),(0,0,1))
    expected_area_weighted = raw_a + raw_b
    expected_area_weighted /= np.linalg.norm(expected_area_weighted)

    # Unweighted unit-average (what the wrong code would produce)
    n_a = np.array([0.0, 0.0, 1.0])
    n_b = np.array([0.0, -1.0, 0.0])
    unit_avg = n_a + n_b
    unit_avg /= np.linalg.norm(unit_avg)

    # The two expectations must be meaningfully different (sanity check)
    assert not np.allclose(expected_area_weighted, unit_avg, atol=0.05)

    # Blended normal must match area-weighted expectation
    assert np.allclose(blended, expected_area_weighted, atol=1e-5)
    # ... and must NOT match the unit average
    assert not np.allclose(blended, unit_avg, atol=0.05)


def test_cube_with_hard_edges_has_per_face_normals():
    # Unit cube: 8 corners, 12 triangles, the 12 cube edges marked hard (NOT the
    # face diagonals). Each corner splits into 3 (one per incident face).
    v = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 1, 1],
        ],
        dtype=np.float32,
    )
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (1, 2, 6, 5),
        (0, 4, 7, 3),
    ]
    tris = []
    hard = set()
    for a, b, c, d in faces:
        tris += [[a, b, c], [a, c, d]]
        for e in [(a, b), (b, c), (c, d), (d, a)]:
            hard.add(frozenset(e))
    tris = np.array(tris, dtype=np.uint32)
    out_pos, out_norm, out_tris = edge_aware_normals(v, tris, hard_edges=hard)
    assert out_pos.shape[0] == 24
    # every normal is axis-aligned (one component +/-1, others 0)
    absn = np.abs(out_norm)
    assert np.allclose(np.sort(absn, axis=1)[:, 2], 1.0)
    assert np.allclose(np.sort(absn, axis=1)[:, :2], 0.0, atol=1e-6)
