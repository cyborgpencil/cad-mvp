#!/usr/bin/env python3
"""Build rust/cadcam_gate for wasm32-unknown-unknown and stage the
wasm-bindgen web glue + .wasm into gitignored web/dist/.
"""
from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

WASM_BINDGEN_VERSION = "0.2.100"
OUT_NAME = "cadcam_rust_gate"
STAGE_FILES = (
    f"{OUT_NAME}.js",
    f"{OUT_NAME}_bg.wasm",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def cargo_env() -> dict[str, str]:
    env = dict(os.environ)
    cargo_bin = Path.home() / ".cargo" / "bin"
    if cargo_bin.is_dir():
        env["PATH"] = f"{cargo_bin}{os.pathsep}{env.get('PATH', '')}"
    return env


def host_wasm_bindgen_archive() -> tuple[str, str]:
    sys_name = platform.system().lower()
    machine = platform.machine().lower()
    if sys_name == "windows":
        triple = "x86_64-pc-windows-msvc"
        exe = "wasm-bindgen.exe"
    elif sys_name == "darwin":
        triple = "aarch64-apple-darwin" if machine in ("arm64", "aarch64") else "x86_64-apple-darwin"
        exe = "wasm-bindgen"
    else:
        triple = "aarch64-unknown-linux-gnu" if machine in ("arm64", "aarch64") else "x86_64-unknown-linux-musl"
        exe = "wasm-bindgen"
    stem = f"wasm-bindgen-{WASM_BINDGEN_VERSION}-{triple}"
    url = f"https://github.com/rustwasm/wasm-bindgen/releases/download/{WASM_BINDGEN_VERSION}/{stem}.tar.gz"
    return url, f"{stem}/{exe}"


def ensure_wasm_bindgen(root: Path, env: dict[str, str]) -> Path:
    which_wb = shutil.which("wasm-bindgen", path=env.get("PATH"))
    if which_wb:
        try:
            out = subprocess.check_output([which_wb, "--version"], env=env, text=True).strip()
            if out.endswith(WASM_BINDGEN_VERSION):
                return Path(which_wb)
        except Exception:
            pass

    cache_dir = root / "builds" / "wasm-bindgen" / WASM_BINDGEN_VERSION
    exe_name = "wasm-bindgen.exe" if platform.system().lower() == "windows" else "wasm-bindgen"
    cached_exe = cache_dir / exe_name
    if cached_exe.is_file():
        return cached_exe

    url, member_suffix = host_wasm_bindgen_archive()
    cache_dir.mkdir(parents=True, exist_ok=True)
    tgz_path = cache_dir / "wasm-bindgen.tar.gz"
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as response:
        tgz_path.write_bytes(response.read())

    with tarfile.open(tgz_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.replace("\\", "/") == member_suffix:
                extracted = tar.extractfile(member)
                if extracted is None:
                    raise RuntimeError(f"Could not extract {member.name}")
                cached_exe.write_bytes(extracted.read())
                if platform.system().lower() != "windows":
                    cached_exe.chmod(0o755)
                break

    if not cached_exe.is_file():
        raise SystemExit(f"Failed to locate {member_suffix} in {tgz_path}")
    return cached_exe


def main() -> int:
    root = repo_root()
    env = cargo_env()
    crate_dir = root / "rust" / "cadcam_gate"
    manifest = crate_dir / "Cargo.toml"
    if not manifest.is_file():
        raise SystemExit(f"Missing Rust crate manifest: {manifest}")

    rustup = shutil.which("rustup", path=env.get("PATH"))
    if rustup:
        subprocess.run(
            [rustup, "target", "add", "wasm32-unknown-unknown"],
            env=env,
            check=True,
        )

    cargo = shutil.which("cargo", path=env.get("PATH"))
    if not cargo:
        raise SystemExit("cargo not found on PATH; install rustup toolchain first.")

    subprocess.run(
        [
            cargo,
            "build",
            "--manifest-path",
            str(manifest),
            "--target",
            "wasm32-unknown-unknown",
            "--release",
        ],
        env=env,
        check=True,
    )

    raw_wasm = crate_dir / "target" / "wasm32-unknown-unknown" / "release" / "cadcam_gate.wasm"
    if not raw_wasm.is_file():
        raise SystemExit(f"Expected built wasm at {raw_wasm}")

    wb_exe = ensure_wasm_bindgen(root, env)
    pkg_dir = root / "builds" / "rust-gate" / "pkg"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            str(wb_exe),
            "--target",
            "web",
            "--no-typescript",
            "--out-dir",
            str(pkg_dir),
            "--out-name",
            OUT_NAME,
            str(raw_wasm),
        ],
        env=env,
        check=True,
    )

    web_dist = root / "web" / "dist"
    web_dist.mkdir(parents=True, exist_ok=True)
    for name in STAGE_FILES:
        src = pkg_dir / name
        if not src.is_file():
            raise SystemExit(f"Missing wasm-bindgen output: {src}")
        dst = web_dist / name
        dst.write_bytes(src.read_bytes())
        print(f"Staged {dst} ({dst.stat().st_size} bytes)")

    staged_wasm = web_dist / f"{OUT_NAME}_bg.wasm"
    sha = hashlib.sha256(staged_wasm.read_bytes()).hexdigest()
    print(f"cadcam_rust_gate ready sha256={sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
