"""
使用 PyInstaller 打包 Flask 后端为独立可执行文件
用于 Tauri sidecar
"""

import os
import sys
import subprocess
import shutil

def build():
    print("=" * 50)
    print("打包 LoArchive 后端服务")
    print("=" * 50)
    
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 目标目录
    output_dir = os.path.join(script_dir, "src-tauri", "binaries")
    os.makedirs(output_dir, exist_ok=True)
    
    # PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # 单文件模式
        "--noconsole",         # 无控制台窗口
        "--clean",             # 清理临时文件
        "--name", "loarchive-backend-x86_64-pc-windows-msvc",  # Tauri sidecar 命名格式
        "--distpath", output_dir,
        "--workpath", os.path.join(script_dir, "build", "pyinstaller"),
        "--specpath", os.path.join(script_dir, "build"),
        # 添加隐式导入
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
        # 主程序
        os.path.join(script_dir, "web_app.py")
    ]
    
    print("\n运行命令:")
    print(" ".join(cmd))
    print()
    
    # 运行 PyInstaller
    result = subprocess.run(cmd, cwd=script_dir)
    
    if result.returncode == 0:
        exe_path = os.path.join(output_dir, "loarchive-backend-x86_64-pc-windows-msvc.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n✅ 打包成功！")
            print(f"   文件: {exe_path}")
            print(f"   大小: {size_mb:.1f} MB")
        else:
            print("\n❌ 打包似乎成功但找不到输出文件")
            return False
    else:
        print(f"\n❌ 打包失败，返回码: {result.returncode}")
        return False
    
    # 清理
    for folder in ["build/pyinstaller", "__pycache__"]:
        path = os.path.join(script_dir, folder)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    
    return True


if __name__ == "__main__":
    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    success = build()
    sys.exit(0 if success else 1)

