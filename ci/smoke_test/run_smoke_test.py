#!/usr/bin/env python3
"""
KLU Smoke Test Runner
Verifies SuiteSparse installation and runs compile/link/analyze/factor/solve smoke tests.
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Run KLU smoke test")
    parser.add_argument(
        "--install-dir",
        type=Path,
        required=True,
        help="Path to installed SuiteSparse directory",
    )
    parser.add_argument(
        "--build-dir",
        type=Path,
        default=Path("_build/klu_smoke"),
        help="Build directory for the smoke test",
    )
    return parser.parse_args()


def check_files(install_dir: Path):
    print("=== 1. Checking installed files ===")
    if not install_dir.exists():
        sys.exit(f"Error: install directory '{install_dir}' does not exist")

    all_files = [p for p in install_dir.rglob("*") if p.is_file()]
    print(f"Total installed files found: {len(all_files)}")

    headers = [p for p in all_files if p.name.lower() == "klu.h"]
    if not headers:
        sys.exit("Error: klu.h not found in install tree")
    print(f"Found klu.h: {[str(h) for h in headers]}")

    system = platform.system()
    static_libs = []
    shared_libs = []

    for p in all_files:
        name = p.name.lower()
        if "klu" in name:
            if system in ("Linux", "Darwin"):
                if p.suffix == ".a":
                    static_libs.append(p)
                elif ".so" in name or p.suffix == ".dylib":
                    shared_libs.append(p)
            elif system == "Windows":
                if p.suffix == ".dll":
                    shared_libs.append(p)
                elif p.suffix == ".lib":
                    static_libs.append(p)

    print(f"KLU static candidates: {[p.name for p in static_libs]}")
    print(f"KLU shared candidates: {[p.name for p in shared_libs]}")

    if not static_libs:
        print("Warning: No static KLU library candidate identified.")
    if not shared_libs:
        print("Warning: No shared KLU library candidate identified.")

    return headers[0].parent


def build_and_run(install_dir: Path, build_dir: Path):
    print("\n=== 2. Configuring and building smoke test ===")
    source_dir = Path(__file__).resolve().parent

    build_dir.mkdir(parents=True, exist_ok=True)

    cmake_configure_cmd = [
        "cmake",
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        f"-DCMAKE_PREFIX_PATH={install_dir.resolve()}",
        "-DCMAKE_BUILD_TYPE=Release",
    ]
    print("Running:", " ".join(cmake_configure_cmd))
    res = subprocess.run(cmake_configure_cmd)
    if res.returncode != 0:
        sys.exit(f"Error: CMake configure failed with exit code {res.returncode}")

    cmake_build_cmd = [
        "cmake",
        "--build",
        str(build_dir),
        "--config",
        "Release",
    ]
    print("Running:", " ".join(cmake_build_cmd))
    res = subprocess.run(cmake_build_cmd)
    if res.returncode != 0:
        sys.exit(f"Error: CMake build failed with exit code {res.returncode}")

    print("\n=== 3. Executing smoke test binaries ===")
    # Look for built executables
    executables = []
    for pattern in ["klu_smoke_shared*", "klu_smoke_static*", "klu_smoke_direct*"]:
        for p in build_dir.rglob(pattern):
            if p.is_file() and not p.name.endswith((".obj", ".o", ".pdb", ".lib", ".ilk")):
                if platform.system() == "Windows":
                    if p.suffix.lower() == ".exe":
                        executables.append(p)
                elif os.access(p, os.X_OK):
                    executables.append(p)

    if not executables:
        sys.exit("Error: No smoke test executables were built")

    # Set up runtime environment
    env = os.environ.copy()
    bin_dir = (install_dir / "bin").resolve()
    lib_dir = (install_dir / "lib").resolve()

    if platform.system() == "Windows":
        path_var = env.get("PATH", "")
        env["PATH"] = f"{bin_dir};{lib_dir};{path_var}"
    elif platform.system() == "Darwin":
        dyld_var = env.get("DYLD_LIBRARY_PATH", "")
        env["DYLD_LIBRARY_PATH"] = f"{lib_dir}:{dyld_var}"
    else:
        ld_var = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = f"{lib_dir}:{ld_var}"

    passed = 0
    for exe in executables:
        print(f"\nRunning test binary: {exe.name} ({exe})")
        proc = subprocess.run([str(exe)], env=env, capture_output=True, text=True)
        print("Output:\n" + proc.stdout)
        if proc.stderr:
            print("Errors/Warnings:\n" + proc.stderr)

        if proc.returncode != 0:
            sys.exit(f"Test {exe.name} failed with returncode {proc.returncode}")
        if "KLU smoke test successfully verified" not in proc.stdout:
            sys.exit(f"Test {exe.name} did not produce expected success string")

        passed += 1

    print(f"\nAll {passed} KLU smoke test target(s) passed successfully!")


def main():
    args = parse_args()
    check_files(args.install_dir)
    build_and_run(args.install_dir, args.build_dir)


if __name__ == "__main__":
    main()
