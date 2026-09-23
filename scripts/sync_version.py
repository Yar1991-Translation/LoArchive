"""版本号单一来源同步：从 loarchive/__init__.py 读取 __version__，
写入 pyproject.toml、package.json 与 src-tauri/tauri.conf.json。

用法：python scripts/sync_version.py [版本号]
不传版本号时读取 __init__.py 的当前值做一次同步（幂等）。
发布工作流在构建前调用，保证三处版本一致。
"""

import json
import re
import sys
from pathlib import Path

# Windows CI / 传统控制台的默认编码（cp1252/cp936）无法输出中文提示
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
INIT_PATH = ROOT / "loarchive" / "__init__.py"
PYPROJECT_PATH = ROOT / "pyproject.toml"
PACKAGE_JSON_PATH = ROOT / "package.json"
TAURI_CONF_PATH = ROOT / "src-tauri" / "tauri.conf.json"


def read_current_version() -> str:
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', INIT_PATH.read_text(encoding="utf-8"), re.M)
    if not match:
        sys.exit(f"未能在 {INIT_PATH} 中找到 __version__")
    return match.group(1)


def sync(version: str) -> None:
    pyproject = PYPROJECT_PATH.read_text(encoding="utf-8")
    pyproject, n = re.subn(r'(?m)^version\s*=\s*"[^"]+"', f'version = "{version}"', pyproject, count=1)
    if n:
        PYPROJECT_PATH.write_text(pyproject, encoding="utf-8")

    for json_path in (PACKAGE_JSON_PATH, TAURI_CONF_PATH):
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if data.get("version") != version:
            data["version"] = version
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    version = sys.argv[1] if len(sys.argv) > 1 else read_current_version()
    if len(sys.argv) > 1:
        # 显式指定版本号时，先回写 __init__.py
        init = INIT_PATH.read_text(encoding="utf-8")
        init, n = re.subn(r'(?m)^__version__\s*=\s*"[^"]+"', f'__version__ = "{version}"', init, count=1)
        if not n:
            sys.exit(f"未能在 {INIT_PATH} 中找到 __version__")
        INIT_PATH.write_text(init, encoding="utf-8")
    sync(version)
    print(f"版本号已同步为 {version}: pyproject.toml, package.json, tauri.conf.json")


if __name__ == "__main__":
    main()
