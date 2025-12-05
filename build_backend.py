"""
Build Flask backend into standalone executable using PyInstaller
For Tauri sidecar
"""

import os
import sys
import subprocess
import shutil

# Fix encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def build():
    print("=" * 50)
    print("Building LoArchive Backend Service")
    print("=" * 50)
    
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Target directory
    output_dir = os.path.join(script_dir, "src-tauri", "binaries")
    os.makedirs(output_dir, exist_ok=True)
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # Single file mode
        "--noconsole",         # No console window
        "--clean",             # Clean temp files
        "--name", "loarchive-backend-x86_64-pc-windows-msvc",  # Tauri sidecar naming format
        "--distpath", output_dir,
        "--workpath", os.path.join(script_dir, "build", "pyinstaller"),
        "--specpath", os.path.join(script_dir, "build"),
        # Hidden imports
        "--hidden-import", "flask",
        "--hidden-import", "flask_cors",
        "--hidden-import", "requests",
        "--hidden-import", "bs4",
        "--hidden-import", "lxml",
        "--hidden-import", "werkzeug",
        "--hidden-import", "jinja2",
        "--hidden-import", "markupsafe",
        "--hidden-import", "itsdangerous",
        "--hidden-import", "click",
        # Main program
        os.path.join(script_dir, "web_app.py")
    ]
    
    print("\nRunning command:")
    print(" ".join(cmd))
    print()
    
    # Run PyInstaller
    result = subprocess.run(cmd, cwd=script_dir)
    
    if result.returncode == 0:
        exe_path = os.path.join(output_dir, "loarchive-backend-x86_64-pc-windows-msvc.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n[SUCCESS] Build completed!")
            print(f"   File: {exe_path}")
            print(f"   Size: {size_mb:.1f} MB")
        else:
            print("\n[ERROR] Build seemed to succeed but output file not found")
            return False
    else:
        print(f"\n[ERROR] Build failed with return code: {result.returncode}")
        return False
    
    # Cleanup
    for folder in ["build/pyinstaller", "__pycache__"]:
        path = os.path.join(script_dir, folder)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    
    return True


if __name__ == "__main__":
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    success = build()
    sys.exit(0 if success else 1)
