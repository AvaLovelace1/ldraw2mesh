import numpy as np

from ldraw2mesh.transform import LDRAW_TO_GLTF, to_gltf_matrix


def test_basis_change_is_proper_rotation():
    assert np.isclose(np.linalg.det(LDRAW_TO_GLTF), 1.0)


def test_basis_change_flips_y_and_z():
    p = np.array([1.0, 2.0, 3.0, 1.0], dtype=np.float32)
    out = LDRAW_TO_GLTF @ p
    assert np.allclose(out, [1.0, -2.0, -3.0, 1.0])


def test_basis_change_is_its_own_inverse():
    assert np.allclose(LDRAW_TO_GLTF @ LDRAW_TO_GLTF, np.eye(4))


def test_to_gltf_matrix_is_column_major():
    m = np.arange(16, dtype=np.float32).reshape(4, 4)  # row-major
    out = to_gltf_matrix(m)
    assert out == m.T.reshape(-1).tolist()
    # translation row of a row-major matrix lands in glTF slots 12,13,14
    t = np.eye(4, dtype=np.float32)
    t[0, 3], t[1, 3], t[2, 3] = 5.0, 6.0, 7.0
    assert to_gltf_matrix(t)[12:15] == [5.0, 6.0, 7.0]
