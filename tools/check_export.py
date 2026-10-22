#!/usr/bin/env python3
"""Check exported STL and 3MF files against a typed size and volume.

Python 3.10 or newer. Exit 0 when every file passes, 1 when any check
prints FAIL, and 2 on a usage or load error. is_watertight is printed
as INFO and never decides the exit code.
"""

from __future__ import annotations

import argparse
import math
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


class LoadError(Exception):
    """The file could not be read as an STL or 3MF mesh."""


def emit(line: str) -> None:
    print(line, flush=True)


def fail(message: str) -> None:
    emit(f"FAIL: {message}")


def passed(message: str) -> None:
    emit(f"PASS: {message}")


def error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr, flush=True)


def fmt(value: float) -> str:
    if not math.isfinite(value):
        return str(value)
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    if text in {"", "-", "-0"}:
        return "0"
    return text


def local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def read_3mf_unit(path: Path) -> str | None:
    """Return the model unit, or None when the attribute is absent."""
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise LoadError(f"{path}: not a readable 3MF zip ({exc}).") from exc
    except OSError as exc:
        raise LoadError(f"{path}: {exc}.") from exc
    with archive:
        model_name = None
        for name in archive.namelist():
            normalized = name.replace("\\", "/").lstrip("/")
            if normalized.lower() == "3d/3dmodel.model":
                model_name = name
                break
        if model_name is None:
            raise LoadError(f"{path}: 3MF is missing 3D/3dmodel.model.")
        try:
            payload = archive.read(model_name)
        except OSError as exc:
            raise LoadError(f"{path}: could not read 3D/3dmodel.model ({exc}).") from exc
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise LoadError(f"{path}: 3D/3dmodel.model is not XML ({exc}).") from exc
    model = root if local_name(root.tag) == "model" else None
    if model is None:
        for element in root.iter():
            if local_name(element.tag) == "model":
                model = element
                break
    if model is None:
        raise LoadError(f"{path}: 3D/3dmodel.model has no model element.")
    for key, value in model.attrib.items():
        if local_name(key) == "unit":
            return value
    return None


def triangle_count(mesh: object) -> int:
    faces = getattr(mesh, "faces", None)
    if faces is None:
        return 0
    return int(len(faces))


def load_mesh(path: Path) -> object:
    import trimesh

    try:
        loaded = trimesh.load_mesh(str(path))
    except Exception as exc:
        raise LoadError(f"{path}: could not load mesh ({exc}).") from exc
    if not isinstance(loaded, trimesh.Trimesh):
        raise LoadError(
            f"{path}: loaded {type(loaded).__name__}, expected a triangle mesh."
        )
    return loaded


def check_file(
    label: str,
    path: Path,
    expect_size: tuple[float, float, float],
    expect_volume: float,
    size_tol: float,
    volume_rel_tol: float,
) -> bool:
    """Print PASS, FAIL, and INFO lines. Return True when nothing failed."""
    suffix = path.suffix.lower()
    if suffix not in {".stl", ".3mf"}:
        raise LoadError(f"{path}: expected an .stl or .3mf file.")
    if not path.is_file():
        raise LoadError(f"{path}: file not found.")

    unit = read_3mf_unit(path) if suffix == ".3mf" else None
    mesh = load_mesh(path)
    emit(label)
    ok = True

    def failed(message: str) -> None:
        nonlocal ok
        ok = False
        fail(message)

    if suffix == ".3mf":
        if unit is None:
            failed("export unit attribute is missing.")
        elif unit != "millimeter":
            failed("export unit is not millimeter.")
        else:
            passed("export unit is millimeter.")

    if triangle_count(mesh) == 0:
        failed("mesh has no triangles.")
    else:
        extents = getattr(mesh, "extents", None)
        if extents is None or len(extents) != 3:
            failed("bbox extents are missing.")
        else:
            actual = (float(extents[0]), float(extents[1]), float(extents[2]))
            if any(not math.isfinite(value) for value in actual) or any(
                abs(got - want) > size_tol for got, want in zip(actual, expect_size)
            ):
                got_text = " ".join(fmt(value) for value in actual)
                want_text = " ".join(fmt(value) for value in expect_size)
                failed(
                    f"bbox extents are {got_text} mm, expected {want_text} mm."
                )
            else:
                got_text = " ".join(fmt(value) for value in actual)
                passed(f"bbox extents are {got_text} mm.")

        volume = float(mesh.volume)
        if not math.isfinite(volume) or volume <= 0.0:
            failed(f"volume is not positive ({fmt(volume)} mm3).")
        else:
            baseline = abs(expect_volume)
            if baseline == 0.0:
                relative = 0.0 if volume == expect_volume else math.inf
            else:
                relative = abs(volume - expect_volume) / baseline
            if relative > volume_rel_tol:
                failed(
                    f"volume is {fmt(volume)} mm3, expected {fmt(expect_volume)} mm3."
                )
            else:
                passed(f"volume is {fmt(volume)} mm3.")

    try:
        watertight = bool(mesh.is_watertight)
        emit(f"INFO: is_watertight is {str(watertight).lower()}.")
    except Exception as exc:
        emit(f"INFO: is_watertight could not be read ({exc}).")
    return ok


def finite_number(name: str, value: float) -> bool:
    if isinstance(value, float) and math.isfinite(value):
        return True
    error(f"{name} must be a finite number.")
    return False


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check STL and 3MF exports against a typed size and volume."
    )
    parser.add_argument("paths", nargs="+", help="One or more .stl or .3mf files.")
    parser.add_argument(
        "--expect-size",
        nargs=3,
        type=float,
        required=True,
        metavar=("X", "Y", "Z"),
        help="Expected axis-aligned bbox extents in millimeters.",
    )
    parser.add_argument(
        "--expect-volume",
        type=float,
        required=True,
        help="Expected volume in mm3 (the app BRepGProp volume).",
    )
    parser.add_argument(
        "--size-tol",
        type=float,
        default=0.1,
        help="Absolute tolerance for each bbox extent, in millimeters (default 0.1).",
    )
    parser.add_argument(
        "--volume-rel-tol",
        type=float,
        default=0.01,
        help="Relative tolerance for volume, |actual-expected|/|expected| (default 0.01).",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    if sys.version_info < (3, 10):
        error("Python 3.10 or newer is required.")
        return 2
    args = parse_args(argv)
    expect_size = (args.expect_size[0], args.expect_size[1], args.expect_size[2])
    if not all(finite_number(f"--expect-size {axis}", value) for axis, value in zip("XYZ", expect_size)):
        return 2
    if not finite_number("--expect-volume", args.expect_volume):
        return 2
    if not finite_number("--size-tol", args.size_tol) or args.size_tol < 0.0:
        if args.size_tol < 0.0:
            error("--size-tol must be zero or positive.")
        return 2
    if not finite_number("--volume-rel-tol", args.volume_rel_tol) or args.volume_rel_tol < 0.0:
        if args.volume_rel_tol < 0.0:
            error("--volume-rel-tol must be zero or positive.")
        return 2

    try:
        import trimesh  # noqa: F401
    except ImportError as exc:
        error(f"trimesh is not installed ({exc}).")
        return 2

    any_fail = False
    load_error = False
    for label in args.paths:
        try:
            if not check_file(
                label,
                Path(label),
                expect_size,
                args.expect_volume,
                args.size_tol,
                args.volume_rel_tol,
            ):
                any_fail = True
        except LoadError as exc:
            error(str(exc))
            load_error = True
    if load_error:
        return 2
    if any_fail:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
