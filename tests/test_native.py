import numpy as np
import pytest

pytestmark = pytest.mark.native


def test_native_module_imports_and_exposes_api():
    from ldraw2mesh import _native

    assert callable(_native.load_file)
    assert callable(_native.load_file_instanced)
    assert callable(_native.load_color_table)


def test_edge_aware_smooth_bend_without_hard_edge_averages():
    from ldraw2mesh import _native

    pos = np.array([[0, 0, 0], [1, 0, 0], [0.5, 1, 0], [0.5, -1, 1]], dtype=np.float32)
    tris = np.array([[0, 1, 2], [1, 0, 3]], dtype=np.uint32)
    hard = np.empty((0, 2), dtype=np.uint32)
    out_pos, out_norm, out_tris = _native.edge_aware_normals(pos, tris, hard)
    assert out_pos.shape[0] == 4  # nothing split
    assert np.allclose(np.linalg.norm(out_norm, axis=1), 1.0)


def test_edge_aware_hard_edge_splits_seam():
    from ldraw2mesh import _native

    pos = np.array([[0, 0, 0], [1, 0, 0], [0.5, 1, 0], [0.5, -1, 1]], dtype=np.float32)
    tris = np.array([[0, 1, 2], [1, 0, 3]], dtype=np.uint32)
    hard = np.array([[0, 1]], dtype=np.uint32)
    out_pos, out_norm, out_tris = _native.edge_aware_normals(pos, tris, hard)
    assert out_pos.shape[0] == 6
    assert out_tris.shape == (2, 3)
    assert set(out_tris[0].tolist()).isdisjoint(out_tris[1].tolist())


def test_edge_aware_area_weighted_blend():
    from ldraw2mesh import _native

    pos = np.array([[0, 0, 0], [4, 0, 0], [0, 4, 0], [0, 0, 1]], dtype=np.float32)
    tris = np.array([[0, 1, 2], [0, 1, 3]], dtype=np.uint32)
    hard = np.empty((0, 2), dtype=np.uint32)
    out_pos, out_norm, out_tris = _native.edge_aware_normals(pos, tris, hard)

    v0_idx = int(out_tris[0, 0])  # output index for original vertex 0
    blended = out_norm[v0_idx]

    expected = np.array([0.0, -4.0, 16.0])  # raw_A + raw_B, area-weighted
    expected /= np.linalg.norm(expected)
    unit_avg = np.array([0.0, -1.0, 1.0])  # the wrong (unit-average) answer
    unit_avg /= np.linalg.norm(unit_avg)

    assert not np.allclose(expected, unit_avg, atol=0.05)  # sanity: they differ
    assert np.allclose(blended, expected, atol=1e-5)
    assert not np.allclose(blended, unit_avg, atol=0.05)


def test_edge_aware_cube_hard_edges_per_face_normals():
    from ldraw2mesh import _native

    v = np.array(
        [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
         [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]],
        dtype=np.float32,
    )
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]
    tris = []
    hard_pairs = set()
    for a, b, c, d in faces:
        tris += [[a, b, c], [a, c, d]]
        for e in [(a, b), (b, c), (c, d), (d, a)]:
            hard_pairs.add(frozenset(e))
    tris = np.array(tris, dtype=np.uint32)
    hard = np.array([sorted(p) for p in hard_pairs], dtype=np.uint32)

    out_pos, out_norm, out_tris = _native.edge_aware_normals(v, tris, hard)
    assert out_pos.shape[0] == 24  # each corner splits into 3 faces
    absn = np.abs(out_norm)
    assert np.allclose(np.sort(absn, axis=1)[:, 2], 1.0)
    assert np.allclose(np.sort(absn, axis=1)[:, :2], 0.0, atol=1e-6)


def test_edge_aware_output_dtypes_and_triangle_shape():
    from ldraw2mesh import _native

    pos = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32)
    tris = np.array([[0, 1, 2]], dtype=np.uint32)
    hard = np.empty((0, 2), dtype=np.uint32)
    out_pos, out_norm, out_tris = _native.edge_aware_normals(pos, tris, hard)
    assert out_pos.dtype == np.float32
    assert out_norm.dtype == np.float32
    assert out_tris.dtype == np.uint32
    assert out_tris.shape == (1, 3)
    assert np.allclose(out_norm[0], [0, 0, 1])  # +Z for CCW triangle in XY plane


def test_edge_aware_degenerate_triangle_yields_zero_normal():
    from ldraw2mesh import _native

    # The normalize() zero-magnitude guard must emit a finite zero vector.
    pos = np.array([[0, 0, 0], [0, 0, 0], [1, 0, 0]], dtype=np.float32)
    tris = np.array([[0, 1, 2]], dtype=np.uint32)
    hard = np.empty((0, 2), dtype=np.uint32)
    out_pos, out_norm, out_tris = _native.edge_aware_normals(pos, tris, hard)
    assert out_tris.shape == (1, 3)
    assert np.all(np.isfinite(out_norm))
    assert np.allclose(out_norm, 0.0)


def test_geometry_settings_defaults_match_upstream():
    from ldraw2mesh import _native

    s = _native.GeometrySettings()
    assert s.triangulate is False
    assert s.weld_vertices is False
    assert s.scene_scale == pytest.approx(1.0)
    # settable (pyclass has set_all)
    s.triangulate = True
    s.scene_scale = 0.0004
    assert s.triangulate is True
    assert s.scene_scale == pytest.approx(0.0004)
