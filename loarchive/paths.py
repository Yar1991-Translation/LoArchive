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
