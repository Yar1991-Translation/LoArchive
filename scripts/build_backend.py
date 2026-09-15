"""Build the LoArchive FastAPI backend into a standalone executable using PyInstaller.

The resulting binary is consumed by the Tauri app as a sidecar
(`src-tauri/binaries/loarchive-backend-<target-triple>[.exe]`).

Usage (from the repository root):
    python scripts/build_backend.py
"""

import io
import os
import shutil
import subprocess
import sys

# Fix encoding for Windows consoles (emoji in build output)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


def build() -> bool:
    print("=" * 50)
    print("Building LoArchive Backend Service")
    print("=" * 50)

    # Ensure we're in the correct directory
    os.chdir(PROJECT_ROOT)

    # Target directory
    output_dir = os.path.join(PROJECT_ROOT, "src-tauri", "binaries")
    os.makedirs(output_dir, exist_ok=True)

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",  # Single file mode
        "--noconsole",  # No console window
        "--clean",  # Clean temp files
        "--name",
        "loarchive-backend-x86_64-pc-windows-msvc",  # Tauri sidecar naming format
        "--distpath",
        output_dir,
        "--workpath",
        os.path.join(PROJECT_ROOT, "build", "pyinstaller"),
        "--specpath",
        os.path.join(PROJECT_ROOT, "build"),
        # Include frontend assets
        "--add-data",
        f"{os.path.join(PROJECT_ROOT, 'frontend')}{os.pathsep}frontend",
        # Hidden imports (uvicorn loads these dynamically at runtime)
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.loops.asyncio",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.http.h11_impl",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.lifespan.on",
        "--hidden-import",
        "uvicorn.lifespan.off",
        "--hidden-import",
        "fastapi",
        "--hidden-import",
        "sse_starlette",
        "--hidden-import",
        "requests",
        "--hidden-import",
        "bs4",
        "--hidden-import",
        "lxml",
        "--hidden-import",
        "lxml.html",
        "--hidden-import",
        "lxml.etree",
        "--hidden-import",
        "html2text",
        "--hidden-import",
        "xhtml2pdf",
        "--hidden-import",
        "reportlab",
        "--hidden-import",
        "ebooklib",
        # Main program
        os.path.join(PROJECT_ROOT, "run.py"),
    ]

    print("\nRunning command:")
    print(" ".join(cmd))
    print()

    result = subprocess.run(cmd, cwd=PROJECT_ROOT, check=False)

    if result.returncode != 0:
        print(f"\n[ERROR] Build failed with return code: {result.returncode}")
        return False

    exe_path = os.path.join(output_dir, "loarchive-backend-x86_64-pc-windows-msvc.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("\n[SUCCESS] Build completed!")
        print(f"   File: {exe_path}")
        print(f"   Size: {size_mb:.1f} MB")
    else:
        print("\n[ERROR] Build seemed to succeed but output file not found")
        return False

    # Cleanup
    for folder in ["build/pyinstaller", "__pycache__"]:
        path = os.path.join(PROJECT_ROOT, folder)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)

    return True


if __name__ == "__main__":
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=False)

    sys.exit(0 if build() else 1)
