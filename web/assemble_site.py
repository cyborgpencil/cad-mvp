#!/usr/bin/env python3
"""Assemble the GitHub Pages site.

This is the only file list. `.github/workflows/pages.yml` and
`tests/deploy_smoke.py` both call `assemble`. Do not keep a second copy
of these names in the workflow.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Site root. `*.mjs` is every module the page loads, including
# occt-gate.mjs, occt-primitives.mjs, occt-ops.mjs, project-file.mjs, selection.mjs, viewport-selection.mjs, assemblies.mjs, and view-cube.mjs.
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
    "project-file.mjs",
    "selection.mjs",
    "viewport-selection.mjs",
    "undo.mjs",
    "assemblies.mjs",
    "view-cube.mjs",
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


_STAMP_RE = re.compile(r"^[A-Za-z0-9._-]{4,40}$")


def build_stamp() -> str:
    """Short git hash, or a UTC build id when git is not available."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root(),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        out = None
    if out is not None and out.returncode == 0:
        stamp = out.stdout.strip()
        if _STAMP_RE.fullmatch(stamp):
            return stamp
    return "b" + time.strftime("%Y%m%d%H%M%S", time.gmtime())


def _with_version(url: str, stamp: str) -> str:
    base, sep, query = url.partition("?")
    parts = [part for part in query.split("&") if part and not part.startswith("v=")]
    parts.append("v=" + stamp)
    return base + "?" + "&".join(parts)


def stamp_static_imports(source: str, stamp: str) -> str:
    """Cache-bust relative .mjs imports in an assembled module."""

    def repl(match: re.Match[str]) -> str:
        return match.group(1) + _with_version(match.group(2), stamp) + match.group(3)

    return re.sub(
        r"""(\bfrom\s+["'])(\./[^"']+\.mjs)(["'])""",
        repl,
        source,
    )


def stamp_page(html: str, stamp: str) -> str:
    """Fill the visible stamp and cache-bust the page's script and module URLs."""
    if not _STAMP_RE.fullmatch(stamp):
        raise SystemExit("refuse to stamp the page with " + stamp)

    def script_src(match: re.Match[str]) -> str:
        return match.group(1) + _with_version(match.group(2), stamp) + match.group(3)

    def module_spec(match: re.Match[str]) -> str:
        return match.group(1) + _with_version(match.group(2), stamp) + match.group(3)

    html = re.sub(
        r'(<script\b[^>]*\bsrc=["\'])([^"\']+)(["\'])',
        script_src,
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r"""(import\s*\(\s*["'])([^"']+)(["']\s*\))""",
        module_spec,
        html,
    )
    stamped, count = re.subn(
        r'(<[^>]*\bid=["\']buildStamp["\'][^>]*>)([^<]*)(</)',
        lambda match: match.group(1) + stamp + match.group(3),
        html,
        count=1,
    )
    if count != 1:
        raise SystemExit("index.html has no build stamp element")
    if f">{stamp}<" not in stamped:
        raise SystemExit("build stamp was not written into the page")
    return stamped


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
    if "index.html" in copied:
        stamp = build_stamp()
        page = dest / "index.html"
        page.write_text(stamp_page(page.read_text(encoding="utf-8"), stamp), encoding="utf-8")
        for rel in ("occt-primitives.mjs", "occt-ops.mjs", "project-file.mjs", "assemblies.mjs"):
            if rel not in copied:
                continue
            module = dest / rel
            module.write_text(
                stamp_static_imports(module.read_text(encoding="utf-8"), stamp),
                encoding="utf-8",
            )
        print(f"build stamp {stamp}")
    (dest / ".nojekyll").write_bytes(b"")
    leaked = (
        dest / "tests" / "fixtures" / "lbracket.json",
        dest / "fixtures" / "lbracket.json",
        dest / "tests" / "fixtures" / "blink.json",
        dest / "fixtures" / "blink.json",
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
