"""通用工具函数。"""

import random
import re

# 本来是随机请求头用的，现在所有页面都要登录，只留一个（沿用 useragentutil 行为）
USER_AGENT_DATAS = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
]

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def get_headers() -> dict:
    """获取请求头（原 useragentutil.get_headers）。"""
    index = random.randint(0, len(USER_AGENT_DATAS) - 1)
    return dict(USER_AGENT_DATAS[index])


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符。"""
    return (
        name.replace("/", "&")
        .replace("|", "&")
        .replace("\\", "&")
        .replace("<", "《")
        .replace(">", "》")
        .replace(":", "：")
        .replace('"', "'")
        .replace("?", "？")
        .replace("*", "·")
        .replace("\n", "")
        .replace("\r", "")
        .replace("\t", " ")
        .strip()
    )


def filter_lofter_image_urls(img_urls: list) -> list:
    """过滤 Lofter 图片 URL，移除缩略图和无效链接。"""
    filtered = []
    for img_url in img_urls:
        if "&amp;" in img_url:
            continue
        if re.search(r"[1649]{2}[x,y][1649]{2}", img_url):
            continue
        img_url = img_url.split("imageView")[0]
        if img_url not in filtered:
            filtered.append(img_url)
    return filtered


def guess_image_type(img_url: str) -> str:
    """按 URL 内容粗略判断图片类型。"""
    if "gif" in img_url:
        return "gif"
    if "png" in img_url:
        return "png"
    return "jpg"
