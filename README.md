# ldraw2mesh

A utility for converting LEGO (LDraw) files to glTF (.glb/.gltf).

Built on [ldr_tools_blender](https://github.com/ScanMountGoat/ldr_tools_blender), but designed to be a standalone tool
without Blender dependencies.

## Installation

```bash
uv add ldraw2mesh       # with uv
pip install ldraw2mesh  # with pip
```

### LDraw Parts Library

An LDraw parts library is required to process LDraw files. Download it
from [https://www.ldraw.org/](https://www.ldraw.org/).

Set the `LDRAW_LIBRARY_PATH` environment variable to the path of your LDraw library:

```bash
export LDRAW_LIBRARY_PATH=/path/to/ldraw
```

## Usage

### Python API

```python
from ldraw2mesh import convert

# Convert an LDraw file to glTF
convert("model.ldr", "model.glb")
```

### Command-line

```bash
ldraw2mesh model.ldr -o model.glb
```

## Contributing

To build from source, you need:

- Rust ≥ 1.85
- `uv`

Clone the repository and run:

```bash
uv run maturin develop --uv
```
