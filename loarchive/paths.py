"""路径解析：资源目录（兼容 PyInstaller）与应用可写数据目录。"""

import os
import sys

APP_NAME = "LoArchive"

# 项目根目录（loarchive 包的上一级）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_frozen() -> bool:
    """是否为 PyInstaller 打包环境。"""
    return getattr(sys, "frozen", False)


def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径，兼容 PyInstaller 打包。"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(PROJECT_ROOT, relative_path)


def get_data_dir() -> str:
    """配置/历史等可写数据目录。

    打包环境写入平台数据目录（避免安装目录只读导致写配置失败），
    源码运行保持当前工作目录（与历史版本行为一致）。
    """
    if is_frozen():
        if sys.platform == "win32":
            base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
            path = os.path.join(base, APP_NAME)
        elif sys.platform == "darwin":
            path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
        else:
            path = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "loarchive")
        os.makedirs(path, exist_ok=True)
        return path
    return os.getcwd()


CONFIG_FILENAME = "loarchive_config.json"
HISTORY_FILENAME = "download_history.json"


def get_executable_dir() -> str:
    """可执行文件所在目录（打包环境用于查找旧版配置）。"""
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return PROJECT_ROOT


def migrate_legacy_data(data_dir: str) -> list:
    """把安装目录旁的旧版配置文件导入新的数据目录（仅打包环境）。

    只在目标文件不存在时复制，绝不覆盖已有数据，也不删除源文件。
    返回实际迁移的文件名列表。
    """
    import shutil

    if not is_frozen():
        return []

    executable_dir = get_executable_dir()
    if os.path.abspath(executable_dir) == os.path.abspath(data_dir):
        return []

    migrated = []
    for filename in (CONFIG_FILENAME, HISTORY_FILENAME):
        source = os.path.join(executable_dir, filename)
        target = os.path.join(data_dir, filename)
        if os.path.exists(source) and not os.path.exists(target):
            try:
                shutil.copy2(source, target)
                migrated.append(filename)
            except Exception as e:
                print(f"迁移旧配置失败 {filename}: {e}")
    return migrated
