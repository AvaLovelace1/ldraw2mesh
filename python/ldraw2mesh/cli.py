"""Command-line interface: ldraw2mesh INPUT -o OUTPUT [options]."""

import argparse
import sys

from .convert import DEFAULT_SCALE, convert
from .library import LDrawLibraryNotFound

__all__ = ["main"]


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ldraw2mesh",
        description="Convert an LDraw file (.ldr/.dat/.mpd) to glTF (.glb/.gltf).",
    )
    p.add_argument("input", help="input LDraw file")
    p.add_argument("-o", "--output", required=True, help="output .glb or .gltf path")
    p.add_argument(
        "--ldraw-library",
        default=None,
        help="path to the LDraw parts library (else $LDRAW_LIBRARY_PATH or common locations)",
    )
    p.add_argument(
        "--scale",
        type=float,
        default=DEFAULT_SCALE,
        help=f"scene scale applied to LDraw units (default {DEFAULT_SCALE}, i.e. LDU->meters)",
    )
    p.add_argument(
        "--studs",
        choices=["normal", "logo", "none", "high-contrast"],
        default="normal",
        help="stud rendering style",
    )
    p.add_argument(
        "--gaps", action="store_true", help="add realistic gaps between parts"
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        convert(
            args.input,
            args.output,
            ldraw_library=args.ldraw_library,
            scale=args.scale,
            studs=args.studs,
            gaps=args.gaps,
        )
    except LDrawLibraryNotFound as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
