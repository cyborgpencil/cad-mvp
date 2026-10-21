#!/usr/bin/env python3
"""Download libcascade 3.1.0 (single-threaded) into gitignored builds/libcascade
and stage the files the web page loads under web/dist/.
"""
from __future__ import annotations

import hashlib
import tarfile
import urllib.request
from pathlib import Path

VERSION = "3.1.0"
TARBALL_URL = "https://registry.npmjs.org/libcascade/-/libcascade-3.1.0.tgz"
WASM_NAME = "opencascade_single.wasm"
WASM_BYTES = 42751732

NEEDED = {
    "package/package.json": "package.json",
    "package/LICENSE": "LICENSE",
    "package/LICENSE.OCCT-Exception": "LICENSE.OCCT-Exception",
    "package/dist/init.single.js": "dist/init.single.js",
    "package/dist/opencascade_single.js": "dist/opencascade_single.js",
    "package/dist/opencascade_single.wasm": "dist/opencascade_single.wasm",
    "package/dist/opencascade_single.provenance.json": "dist/opencascade_single.provenance.json",
}

STAGE = [
    "dist/init.single.js",
    "dist/opencascade_single.js",
    "dist/opencascade_single.wasm",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as response:
        data = response.read()
    dest.write_bytes(data)
    print(f"Wrote {dest} ({len(data)} bytes)")


def extract(tgz: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tgz, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name not in NEEDED:
                continue
            rel = NEEDED[member.name]
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            extracted = tar.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"Could not extract {member.name}")
            out.write_bytes(extracted.read())
            print(f"Extracted {rel} ({out.stat().st_size} bytes)")


def stage_web(lib_root: Path, web_dist: Path) -> None:
    web_dist.mkdir(parents=True, exist_ok=True)
    for rel in STAGE:
        src = lib_root / rel
        dst = web_dist / Path(rel).name
        dst.write_bytes(src.read_bytes())
        print(f"Staged {dst} ({dst.stat().st_size} bytes)")


def main() -> int:
    root = repo_root()
    lib_root = root / "builds" / "libcascade"
    tgz = lib_root / "libcascade-3.1.0.tgz"
    wasm = lib_root / "dist" / WASM_NAME
    web_dist = root / "web" / "dist"

    if not wasm.exists() or wasm.stat().st_size != WASM_BYTES:
        if not tgz.exists():
            download(TARBALL_URL, tgz)
        extract(tgz, lib_root)
        (lib_root / "VERSION.txt").write_text(
            "\n".join(
                [
                    "name=libcascade",
                    f"version={VERSION}",
                    f"url={TARBALL_URL}",
                    "npm=https://www.npmjs.com/package/libcascade/v/3.1.0",
                    "occt=V8_0_1",
                    "variant=single-threaded",
                    "emscripten=6.0.5",
                    f"wasm=dist/{WASM_NAME}",
                    f"wasm_bytes={WASM_BYTES}",
                    "",
                ]
            ),
            encoding="ascii",
        )
    else:
        print(f"Using existing {wasm} ({wasm.stat().st_size} bytes)")

    if not wasm.exists() or wasm.stat().st_size != WASM_BYTES:
        raise SystemExit(f"Expected {WASM_NAME} of {WASM_BYTES} bytes")

    stage_web(lib_root, web_dist)
    sha = hashlib.sha256(wasm.read_bytes()).hexdigest()
    print(f"libcascade {VERSION} single-threaded ready sha256={sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
