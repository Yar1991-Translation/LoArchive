"""LoArchive 启动入口（开发与 PyInstaller 打包共用）。"""

import io
import sys

# Windows 终端 UTF-8 编码修复 — 防止 emoji 字符导致 GBK 编码崩溃
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from loarchive.main import run  # noqa: E402

if __name__ == "__main__":
    run()
