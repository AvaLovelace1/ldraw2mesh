"""Convert LDraw files to glTF (.glb/.gltf)."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ldraw2mesh")
except PackageNotFoundError:  # editable/source checkout without metadata
    __version__ = "0.0.0.dev0"

from .convert import convert, load_scene

__all__ = ["__version__", "convert", "load_scene"]
