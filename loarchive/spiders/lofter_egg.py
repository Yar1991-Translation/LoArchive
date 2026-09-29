"""Lofter 彩蛋（回礼 ReturnGift）内容下载。

机制（依据 Loftify 客户端逆向整理，见 issue #2）：作者在帖子上挂一份隐藏
内容（回礼），读者送礼解锁后可见。移动端 API（api.lofter.com，请求头鉴权）：

    GET /v1.1/trade/gift/post/newSupportInfo?postId=&blogId=&scene=note
        → data.returnGifts[]（未解锁时只有预览 digest）、
          data.gainReturnGifts[]（当前账户已解锁的回礼）
    GET /v1.1/trade/gift/myReturnGift?postId=&blogId=&id=<returnGiftId>
        → data.plan.content / data.plan.images（解锁后的正文与图片）

帖子网页 URL 中的 id 即数字 ID 的十六进制：
    https://<blog>.lofter.com/post/<hex(blogId)>_<hex(postId)>

安全原则：本模块绝不调用 /v1.1/trade/gift/present（送礼支付接口，会消耗
粮票/金币）。只下载"当前账户已解锁"的彩蛋；未解锁的跳过并在任务日志说明。

范围：仅接入单篇保存流程（single_img / single_txt）。作者文章、喜欢/推荐
等批量流程一次涉及大量帖子，为避免高频请求暂不启用。
"""

import os
import re
import time

import requests

from ..errors import FetchError
from ..logsetup import get_logger
from ..utils import sanitize_filename
from .common import DOWNLOAD_TIMEOUT, download_file, guess_image_type, unique_file_path

logger = get_logger("spider.egg")

POST_URL_PATTERN = re.compile(r"lofter\.com/post/([0-9a-fA-F]+)_([0-9a-fA-F]+)")

# 移动端彩蛋接口的公共头（参照 Loftify：lofproduct 跟随其常量）
EGG_API_ORIGIN = "https://api.lofter.com"
EGG_UA = "LOFTER-Android 8.0.12"
EGG_PRODUCT = "lofter-android-8.0.12"

# 网页登录方式（LOFTER_SESS / NTES_SESS）没有对应的移动端鉴权头，
# 仅以 cookie 形式携带；能否通过接口鉴权未经验证，失败时建议改用
# 手机号或 Lofter ID 登录方式。
WEB_LOGIN_KEYS = {"LOFTER_SESS", "NTES_SESS"}


def parse_post_ids(post_url: str) -> tuple[int | None, int | None]:
    """从帖子网页 URL 解析 (postId, blogId)；非标准帖子链接返回 (None, None)。

    网页 id 两段均为数字 ID 的十六进制（NumberUtil.intToHex = toRadixString(16)）。
    """
    match = POST_URL_PATTERN.search(post_url)
    if not match:
        return None, None
    try:
        post_id = int(match.group(2), 16)
        blog_id = int(match.group(1), 16)
    except ValueError:
        return None, None
    return post_id, blog_id


def build_egg_headers(config: dict) -> dict:
    """按登录方式构造移动端 API 鉴权头（TokenType 对照见模块 docstring）。"""
    login_key = config.get("login_key", "")
    login_auth = config.get("login_auth", "")
    headers = {
        "User-Agent": EGG_UA,
        "lofproduct": EGG_PRODUCT,
    }
    if login_key == "LOFTER-PHONE-LOGIN-AUTH":
        headers["lofter-phone-login-auth"] = login_auth
    elif login_key == "Authorization":
        headers["Authorization"] = login_auth
    return headers


def build_egg_session(config: dict) -> requests.Session:
    """彩蛋接口专用会话：直连（绕过系统代理，与 DWR 同款要求）+ 鉴权。"""
    session = requests.Session()
    session.trust_env = False
    session.headers.update(build_egg_headers(config))
    login_key = config.get("login_key", "")
    if login_key in WEB_LOGIN_KEYS:
        session.cookies.set(login_key, config.get("login_auth", ""), domain=".lofter.com")
    return session


def _ms() -> int:
    return int(time.time() * 1000)


def _get_json(session: requests.Session, path: str, params: dict) -> dict:
    """GET 彩蛋接口并校验 trade 系响应包络（code==200 && ok==true）。"""
    params = {**params, "_": _ms()}
    response = session.get(EGG_API_ORIGIN + path, params=params, timeout=DOWNLOAD_TIMEOUT)
    if response.status_code != 200:
        raise FetchError(f"HTTP {response.status_code}")
    try:
        payload = response.json()
    except ValueError as e:
        raise FetchError("响应不是 JSON（登录态可能已失效）") from e
    if payload.get("code") != 200 or payload.get("ok") is not True:
        raise FetchError(payload.get("msg") or f"code={payload.get('code')}")
    return payload.get("data") or {}


def parse_unlocked_eggs(data: dict) -> list[dict]:
    """从 newSupportInfo 的 data 中筛出当前账户已解锁的彩蛋（纯函数）。

    已解锁判定：returnGifts 条目自带 content，或其 id 出现在 gainReturnGifts。
    """
    gain_ids = {gift.get("id") for gift in (data.get("gainReturnGifts") or []) if gift.get("id") is not None}
    unlocked = []
    for gift in data.get("returnGifts") or []:
        if not gift.get("id"):
            continue
        if gift.get("content") or gift.get("id") in gain_ids:
            unlocked.append(gift)
    return unlocked


def parse_return_gift(plan: dict) -> dict:
    """把 myReturnGift 的 data.plan 解析为 {title, content, images}（纯函数）。"""
    images = []
    for image in plan.get("images") or []:
        url = image.get("raw") or image.get("baseImage") or ""
        if url:
            images.append(url)
    return {
        "title": plan.get("title") or "",
        "content": plan.get("content") or "",
        "plan_type": (plan.get("planType") or {}).get("name") or "彩蛋",
        "images": images,
    }


def _save_egg(ctx, egg: dict, post_url: str, text_dir: str, image_dir: str) -> None:
    """把一个已解锁彩蛋落盘：正文写 txt，图片逐张下载。"""
    title = sanitize_filename(egg["title"]) or "无标题"
    os.makedirs(text_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)

    head = f"{egg['title'] or '无标题'}（{egg['plan_type']}）\n原帖链接：{post_url}\n"
    head += "=" * 50 + "\n\n"
    txt_path = unique_file_path(text_dir, f"彩蛋-{title}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(head + egg["content"])
    ctx.log(f"   🥚 已保存彩蛋: {os.path.basename(txt_path)}")

    for index, image_url in enumerate(egg["images"]):
        image_path = unique_file_path(image_dir, f"彩蛋-{title}({index + 1}).{guess_image_type(image_url)}")
        try:
            download_file(image_url, image_path, referer=post_url)
            ctx.log(f"   🥚 已保存彩蛋图片: {os.path.basename(image_path)}")
        except Exception as e:
            logger.warning("下载彩蛋图片失败 %s: %s", image_url, e)
            ctx.log(f"   ⚠️ 彩蛋图片下载失败: {os.path.basename(image_path)}")


def download_eggs_for_post(ctx, post_url: str, text_dir: str, image_dir: str) -> None:
    """检查并下载一个帖子上"当前账户已解锁"的彩蛋。绝不抛异常、绝不支付。

    未解锁的彩蛋只提示跳过——解锁（送礼支付）需要用户在 Lofter 客户端
    自行完成，这正是 issue #2 中确认的前提。
    """
    post_id, blog_id = parse_post_ids(post_url)
    if post_id is None or blog_id is None:
        return

    try:
        session = build_egg_session(ctx.config)
        data = _get_json(
            session,
            "/v1.1/trade/gift/post/newSupportInfo",
            {"postId": post_id, "blogId": blog_id, "vipFans": 0, "openFansVipPlan": 0, "scene": "note"},
        )
    except Exception as e:
        logger.warning("彩蛋信息获取失败 %s: %s", post_url, e)
        ctx.log(f"   ⚠️ 彩蛋信息获取失败: {e}")
        return

    unlocked = parse_unlocked_eggs(data)
    all_gifts = data.get("returnGifts") or []
    if not all_gifts:
        return  # 该帖没有彩蛋

    locked_count = len(all_gifts) - len(unlocked)
    saved_count = 0
    for gift in unlocked:
        try:
            if gift.get("content"):
                plan = gift
            else:
                data_plan = _get_json(
                    session,
                    "/v1.1/trade/gift/myReturnGift",
                    {"postId": post_id, "blogId": blog_id, "id": gift["id"]},
                )
                plan = data_plan.get("plan") or {}
            egg = parse_return_gift(plan)
            if not egg["content"] and not egg["images"]:
                logger.warning("彩蛋 %s 内容为空，跳过", gift["id"])
                continue
            _save_egg(ctx, egg, post_url, text_dir, image_dir)
            saved_count += 1
        except Exception as e:
            logger.warning("彩蛋 %s 保存失败: %s", gift.get("id"), e)
            ctx.log(f"   ⚠️ 彩蛋保存失败: {e}")

    if locked_count:
        ctx.log(f"   🔒 有 {locked_count} 个彩蛋未解锁，已跳过（需先在 Lofter 中解锁再重新下载）")
    if saved_count or locked_count:
        ctx.log(
            f"   🥚 彩蛋处理完成: 保存 {saved_count} 个" + (f"，跳过未解锁 {locked_count} 个" if locked_count else "")
        )
