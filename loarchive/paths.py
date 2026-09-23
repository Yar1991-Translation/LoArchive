"""路径解析：资源目录（兼容 PyInstaller）与应用可写数据目录。"""

import os
import sys

from .logsetup import get_logger

logger = get_logger("paths")

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
    """配置/历史等可写数据目录（平台应用数据目录）。

    打包与源码运行统一使用平台数据目录：配置里含 Lofter 登录令牌，
    不应落在源码根目录或安装目录。首次启动时由 migrate_legacy_data
    从旧位置（安装目录旁 / 源码根目录）导入。
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
        path = os.path.join(base, APP_NAME)
    elif sys.platform == "darwin":
        path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    else:
        path = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "loarchive")
    os.makedirs(path, exist_ok=True)
    return path


CONFIG_FILENAME = "loarchive_config.json"
HISTORY_FILENAME = "download_history.json"  # 旧版 JSON（仅作迁移来源）
HISTORY_DB_FILENAME = "history.db"  # v2 起的 SQLite 存储


def get_executable_dir() -> str:
    """可执行文件所在目录（打包环境用于查找旧版配置）。"""
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return PROJECT_ROOT


def migrate_legacy_data(data_dir: str) -> list:
    """把旧位置的配置文件导入数据目录（仅默认数据目录的首启迁移会调用）。

    候选来源：可执行文件所在目录（打包环境）与当前工作目录（源码运行，
    历史版本把配置放在源码根目录）。只在目标文件不存在时复制，
    绝不覆盖已有数据，也不删除源文件。返回实际迁移的文件名列表。
    """
    import shutil

    candidate_dirs = [get_executable_dir(), os.getcwd()]
    if all(os.path.abspath(d) == os.path.abspath(data_dir) for d in candidate_dirs):
        return []

    migrated = []
    for filename in (CONFIG_FILENAME, HISTORY_FILENAME):
        target = os.path.join(data_dir, filename)
        if os.path.exists(target):
            continue
        for source_dir in candidate_dirs:
            source = os.path.join(source_dir, filename)
            if os.path.exists(source):
                try:
                    shutil.copy2(source, target)
                    migrated.append(filename)
                    break
                except Exception as e:
                    logger.warning("迁移旧配置失败 %s: %s", filename, e)
    return migrated
