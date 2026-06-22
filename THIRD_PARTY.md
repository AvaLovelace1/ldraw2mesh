# Third-party code

`src/lib.rs` is vendored from **[ldr_tools_blender](https://github.com/ScanMountGoat/ldr_tools_blender)**
(`ldr_tools_py/src/lib.rs`) at revision `ee0a1a6`, with the PyO3 module renamed to `_native`.
Copyright (c) 2023 SMG. MIT License.

The wheel also statically links the Rust crates **ldr_tools** (rev `ee0a1a6`, ScanMountGoat/ldr_tools_blender, MIT)
and **map_py** (rev `2dea8c4`, ScanMountGoat/map_py).
