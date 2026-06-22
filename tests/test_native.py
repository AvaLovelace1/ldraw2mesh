import pytest

pytestmark = pytest.mark.native


def test_native_module_imports_and_exposes_api():
    from ldraw2mesh import _native

    assert callable(_native.load_file)
    assert callable(_native.load_file_instanced)
    assert callable(_native.load_color_table)


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
