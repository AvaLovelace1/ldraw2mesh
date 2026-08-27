"""Convert LDraw files to glTF (.glb/.gltf)."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ldraw2mesh")
except PackageNotFoundError:  # editable/source checkout without metadata
    __version__ = "0.0.0.dev0"

from .convert import EmptySceneError, convert, load_scene
from .library import LDrawLibraryNotFound

__all__ = [
    "EmptySceneError",
    "LDrawLibraryNotFound",
    "__version__",
    "convert",
    "load_scene",
]
