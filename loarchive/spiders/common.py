"""爬虫公共逻辑：保存路径、文件名去重、图片类型、Lofter 图片匹配与文件下载。"""

import os
import re

import requests

from ..logsetup import get_logger
from ..utils import get_headers, guess_image_type  # noqa: F401  (re-export 供各爬虫统一 import)

logger = get_logger("spider")

# Lofter 图片 CDN 链接。注意：沿用原实现中的未转义点号（\. 会漏掉真实存在的
# imglf1.lf127.net 这类主机名，原模式靠通配点号偶然匹配正确），不要“修正”它。
LOFTER_IMG_PATTERN = re.compile(r'"(http[s]{0,1}://imglf\d{0,1}.lf\d*.[0-9]{0,3}.net.*?)"')

DOWNLOAD_TIMEOUT = 30


def save_root(ctx) -> str:
    """用户配置的保存根目录。"""
    return ctx.config.get("save_path", "./dir")


def unique_file_path(directory: str, filename: str) -> str:
    """目标目录下的不重复文件路径：重名时追加 (1)、(2)……"""
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        return path
    stem, dot, ext = filename.rpartition(".")
    if not dot:
        stem, ext = filename, ""
    counter = 1
    while os.path.exists(path):
        suffix = f"({counter})" + (f".{ext}" if ext else "")
        path = os.path.join(directory, f"{stem}{suffix}")
        counter += 1
    return path


def download_file(url: str, dest_path: str, referer: str = "", cookies: dict | None = None) -> None:
    """下载文件到 dest_path；失败抛异常，由调用方决定如何记录。"""
    headers = get_headers()
    if referer:
        headers["Referer"] = referer
    response = requests.get(url, headers=headers, cookies=cookies, timeout=DOWNLOAD_TIMEOUT)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(response.content)
