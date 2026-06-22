from typing import Final, Literal, TypeAlias

import numpy as np

UByteArray: TypeAlias = "np.ndarray[tuple[int], np.dtype[np.uint8]]"
UIntArray: TypeAlias = "np.ndarray[tuple[int], np.dtype[np.uint32]]"
FloatArray: TypeAlias = "np.ndarray[tuple[int], np.dtype[np.float32]]"
UVec2Array: TypeAlias = "np.ndarray[tuple[int, Literal[2]], np.dtype[np.uint32]]"
Vec2Array: TypeAlias = "np.ndarray[tuple[int, Literal[2]], np.dtype[np.float32]]"
Vec3Array: TypeAlias = "np.ndarray[tuple[int, Literal[3]], np.dtype[np.float32]]"
Mat4: TypeAlias = "np.ndarray[tuple[Literal[4], Literal[4]], np.dtype[np.float32]]"
Mat4Array: TypeAlias = (
    "np.ndarray[tuple[int, Literal[4], Literal[4]], np.dtype[np.float32]]"
)

class StudType:
    Disabled: Final[StudType]
    Normal: Final[StudType]
    Logo4: Final[StudType]
    HighContrast: Final[StudType]

class PrimitiveResolution:
    Low: Final[PrimitiveResolution]
    Normal: Final[PrimitiveResolution]
    High: Final[PrimitiveResolution]

class LDrawPath:
    name: str
    normalized_name: str

class LDrawNode:
    name: str
    transform: Mat4
    geometry_name: LDrawPath | None
    current_color: int
    children: list[LDrawNode]

class LDrawTextureInfo:
    textures: list[bytes]
    indices: UByteArray
    uvs: Vec2Array

class LDrawGeometry:
    vertices: Vec3Array
    vertex_indices: UIntArray
    face_start_indices: UIntArray
    face_sizes: UIntArray
    face_colors: UIntArray
    is_face_stud: list[bool]
    edge_line_indices: UVec2Array
    has_grainy_slopes: bool
    texture_info: LDrawTextureInfo | None

class LDrawColor:
    name: str
    finish_name: str
    rgba_linear: tuple[float, float, float, float]
    speckle_rgba_linear: tuple[float, float, float, float] | None

class GeometrySettings:
    triangulate: bool
    add_gap_between_parts: bool
    stud_type: StudType
    weld_vertices: bool
    primitive_resolution: PrimitiveResolution
    scene_scale: float
    def __init__(self) -> None: ...

class LDrawScene:
    root_node: LDrawNode
    geometry_cache: dict[LDrawPath, LDrawGeometry]

class LDrawSceneInstanced:
    main_model_name: str
    geometry_world_transforms: dict[tuple[LDrawPath, int], Mat4Array]
    geometry_cache: dict[LDrawPath, LDrawGeometry]

def load_file(
    path: str, ldraw_path: str, additional_paths: list[str], settings: GeometrySettings
) -> LDrawScene: ...
def load_file_instanced(
    path: str, ldraw_path: str, additional_paths: list[str], settings: GeometrySettings
) -> LDrawSceneInstanced: ...
def load_color_table(ldraw_path: str) -> dict[int, LDrawColor]: ...
