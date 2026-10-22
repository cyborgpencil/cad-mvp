#!/usr/bin/env python3
"""Assemble the GitHub Pages site.

This is the only file list. `.github/workflows/pages.yml` and
`tests/deploy_smoke.py` both call `assemble`. Do not keep a second copy
of these names in the workflow.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Site root. `*.mjs` is every module the page loads, including
# occt-gate.mjs, occt-primitives.mjs, occt-ops.mjs, selection.mjs, and viewport-selection.mjs.
ROOT_GLOBS = ("index.html", "cadcam.js", "cadcam.wasm", "*.mjs")

# Staged by web/fetch-libcascade.py. The page imports these paths.
DIST_FILES = (
    "dist/init.single.js",
    "dist/opencascade_single.js",
    "dist/opencascade_single.wasm",
)

# Names that must be in the tree. A new import has to land in this tuple
# or the glob above. Missing any of these fails the assemble.
REQUIRED = (
    "index.html",
    "cadcam.js",
    "cadcam.wasm",
    "occt-gate.mjs",
    "occt-primitives.mjs",
    "occt-ops.mjs",
    "selection.mjs",
    "viewport-selection.mjs",
    "dist/init.single.js",
    "dist/opencascade_single.js",
    "dist/opencascade_single.wasm",
    ".nojekyll",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def reject_off_site(rel: str) -> None:
    """The site is web/ only. tests/ and fixtures/ are never published."""
    norm = rel.replace("\\", "/").lstrip("./")
    if (
        norm == "tests"
        or norm.startswith("tests/")
        or norm == "fixtures"
        or norm.startswith("fixtures/")
    ):
        raise SystemExit("refuse to copy tests/ or fixtures/ into the site: " + norm)


def manifest(web: Path | None = None) -> list[str]:
    """Site-relative paths, in copy order. Globs are sorted."""
    web = web or (repo_root() / "web")
    names: list[str] = []
    seen: set[str] = set()

    def add(rel: str, path: Path) -> None:
        if not path.is_file():
            raise SystemExit(f"missing {path}")
        reject_off_site(rel)
        if rel not in seen:
            seen.add(rel)
            names.append(rel)

    for pattern in ROOT_GLOBS:
        matches = sorted(web.glob(pattern))
        if not matches:
            raise SystemExit(f"missing web/{pattern}")
        for path in matches:
            if path.is_file():
                add(path.name, path)
    for rel in DIST_FILES:
        add(rel, web / rel)
    return names


def assemble(dest: Path, omit: list[str] | None = None) -> list[str]:
    """Copy the Pages tree into `dest` (a directory named `_site`).

    `omit` drops site-relative paths after the manifest is resolved.
    The deploy workflow passes no omit. The smoke test uses it only
    for a temporary negative check.
    """
    if dest.name != "_site":
        raise SystemExit(f"refuse to assemble into {dest}; the directory must be named _site")
    root = repo_root()
    web = root / "web"
    planned = manifest(web)
    skipped = {item.replace("\\", "/") for item in (omit or [])}
    unknown = sorted(skipped - set(planned))
    if unknown:
        raise SystemExit("omit is not in the site list: " + ", ".join(unknown))

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    copied: list[str] = []
    for rel in planned:
        if rel in skipped:
            continue
        reject_off_site(rel)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(web / rel, target)
        copied.append(rel)
    (dest / ".nojekyll").write_bytes(b"")
    leaked = (
        dest / "tests" / "fixtures" / "lbracket.json",
        dest / "fixtures" / "lbracket.json",
    )
    for path in leaked:
        if path.exists():
            raise SystemExit(f"refuse to publish {path}")

    present = set(copied)
    present.add(".nojekyll")
    missing = [name for name in REQUIRED if name not in present and name not in skipped]
    if missing:
        raise SystemExit("site is missing " + ", ".join(missing))
    return copied + [".nojekyll"]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: assemble_site.py DEST", file=sys.stderr)
        return 2
    dest = Path(argv[1])
    if not dest.is_absolute():
        dest = repo_root() / dest
    files = assemble(dest)
    print(f"assembled {dest} ({len(files)} files)")
    for rel in files:
        print(rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
