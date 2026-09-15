"""Lofter 喜欢/推荐/Tag 内容爬取。"""

import ast
import os
import re
import time

import requests
from lxml.html import etree

from ..exporters.pdf import generate_lofter_pdf
from ..utils import CHROME_UA, get_headers, sanitize_filename


def parse_fav_info(fav_info: str):
    """解析单条 DWR 返回的博客信息（纯函数），失败返回 None。"""
    try:
        # 博客链接
        blog_url = re.search(r's\d{1,5}.blogPageUrl="(.*?)"', fav_info)
        if not blog_url:
            return None
        blog_url = blog_url.group(1)

        # 作者名
        author_name_search = re.search(r's\d{1,5}.blogNickName="(.*?)"', fav_info)
        if author_name_search:
            author_name = author_name_search.group(1).encode("latin-1").decode("unicode_escape", errors="replace")
        else:
            author_name = "未知作者"

        # 作者IP
        author_ip = re.search(r"http[s]{0,1}://(.*?).lofter.com", blog_url).group(1)

        # 发表时间
        public_timestamp = re.search(r"s\d{1,5}.publishTime=(.*?);", fav_info)
        if public_timestamp:
            time_local = time.localtime(int(int(public_timestamp.group(1)) / 1000))
            public_time = time.strftime("%Y-%m-%d", time_local)
        else:
            public_time = "未知时间"

        # 图片链接
        img_urls = []
        urls_search = re.search(r'originPhotoLinks="(\[.*?\])"', fav_info)
        if urls_search:
            try:
                urls_str = urls_search.group(1).replace("\\", "").replace("false", "False").replace("true", "True")
                urls_infos = ast.literal_eval(urls_str)
                for url_info in urls_infos:
                    img_url = url_info.get("raw", "") or url_info.get("orign", "").split("?imageView")[0]
                    if img_url:
                        img_urls.append(img_url)
            except Exception:
                pass

        # 正文内容
        content_search = re.search(r's\d{1,5}.content="(.*?)";', fav_info)
        if content_search:
            content = content_search.group(1).encode("latin-1").decode("unicode_escape", errors="ignore")
            try:
                import html2text

                h = html2text.HTML2Text()
                h.ignore_links = False
                content = h.handle(content)
            except Exception:
                pass
        else:
            content = ""

        # 标题
        title_search = re.search(r's\d{1,5}.title="(.*?)"', fav_info)
        title = ""
        if title_search:
            title = title_search.group(1).encode("latin-1").decode("unicode_escape", errors="ignore")

        return {
            "url": blog_url,
            "author_name": author_name,
            "author_ip": author_ip,
            "public_time": public_time,
            "img_urls": img_urls,
            "content": content,
            "title": title,
            "has_img": len(img_urls) > 0,
        }

    except Exception:
        return None


def _build_request(mode: str, url: str):
    """按模式构建 DWR 请求 URL 与 Referer（纯函数）。"""
    if mode == "like2":
        return "http://www.lofter.com/dwr/call/plaincall/PostBean.getFavTrackItem.dwr", "http://www.lofter.com/like"
    if mode == "like1":
        user_name = re.search(r"http[s]{0,1}://(.*?).lofter.com/", url).group(1)
        return (
            "https://www.lofter.com/dwr/call/plaincall/BlogBean.queryLikePosts.dwr",
            "https://www.lofter.com/favblog/" + user_name,
        )
    if mode == "share":
        user_name = re.search(r"http[s]{0,1}://(.*?).lofter.com/", url).group(1)
        return (
            "https://www.lofter.com/dwr/call/plaincall/BlogBean.querySharePosts.dwr",
            "https://www.lofter.com/shareblog/" + user_name,
        )
    if mode == "tag":
        return "http://www.lofter.com/dwr/call/plaincall/TagBean.search.dwr", url
    return None, None


def _build_data_params(mode: str, url: str, user_id: str, get_num: int, got_num: int) -> dict:
    """按模式构建 DWR 请求参数（纯函数）。"""
    if mode in ["like1", "share"]:
        return {
            "c0-scriptName": "BlogBean",
            "c0-methodName": "queryLikePosts" if mode == "like1" else "querySharePosts",
            "c0-param0": "number:" + str(user_id),
            "c0-param1": "number:" + str(get_num),
            "c0-param2": "number:" + str(got_num),
            "c0-param3": "string:",
        }
    if mode == "like2":
        return {
            "c0-scriptName": "PostBean",
            "c0-methodName": "getFavTrackItem",
            "c0-param0": "number:" + str(get_num),
            "c0-param1": "number:" + str(got_num),
        }
    if mode == "tag":
        url_search = re.search(r"http[s]{0,1}://www.lofter.com/tag/(.*?)/(.*)", url)
        if url_search:
            tag_name = url_search.group(1)
            tag_type = url_search.group(2) if url_search.group(2) else "new"
        else:
            url_search = re.search(r"http[s]{0,1}://www.lofter.com/tag/(.*)", url)
            tag_name = url_search.group(1) if url_search else ""
            tag_type = "new"

        return {
            "c0-scriptName": "TagBean",
            "c0-methodName": "search",
            "c0-param0": "string:" + tag_name,
            "c0-param1": "number:0",
            "c0-param2": "string:",
            "c0-param3": "string:" + tag_type,
            "c0-param4": "boolean:false",
            "c0-param5": "number:0",
            "c0-param6": "number:" + str(get_num),
            "c0-param7": "number:" + str(got_num),
            "c0-param8": "number:" + str(int(time.time() * 1000)),
            "batchId": "870178",
        }
    return {}


def run_like_share_tag(ctx, params: dict) -> None:
    """运行喜欢/推荐/Tag爬取任务。"""
    url = params.get("url", "")
    mode = params.get("mode", "like2")  # like1, like2, share, tag
    save_mode = params.get("save_mode", {"article": 1, "text": 1, "long article": 1, "img": 1})
    export_pdf = params.get("export_pdf", False)  # 是否导出PDF

    if not url:
        ctx.log("❌ 请提供链接地址")
        return

    ctx.log(f"🚀 开始 {mode} 模式爬取任务")
    ctx.log(f"📍 URL: {url}")

    login_key = ctx.config["login_key"]
    login_auth = ctx.config["login_auth"]

    try:
        # 获取登录session
        ctx.log("🔐 正在建立登录会话...")

        headers = {
            "User-Agent": CHROME_UA,
            "Host": "www.lofter.com",
        }

        session = requests.session()
        session.headers = headers
        session.cookies.set(login_key, login_auth)

        # 根据模式确定请求URL和参数
        requests_url, referer = _build_request(mode, url)
        if requests_url is None:
            ctx.log(f"❌ 不支持的模式: {mode}")
            return
        headers["Referer"] = referer

        session.headers = headers

        # 获取用户ID (like1, share 模式需要)
        user_id = ""
        if mode in ["like1", "share"]:
            ctx.log("📖 获取用户信息...")
            host = re.search(r"https://(.*?)/", url).group(1)
            session.headers["Host"] = host
            user_page = session.get(url).content.decode("utf-8")
            user_page_parse = etree.HTML(user_page)
            try:
                user_id = user_page_parse.xpath("//body/iframe[@id='control_frame']/@src")[0].split("blogId=")[1]
                ctx.log(f"   用户ID: {user_id}")
            except Exception:
                ctx.log("❌ 无法获取用户ID，请检查链接是否正确")
                return
            session.headers["Host"] = "www.lofter.com"

        # 构建初始请求参数
        base_data = {
            "callCount": "1",
            "httpSessionId": "",
            "scriptSessionId": "${scriptSessionId}187",
            "c0-id": "0",
            "batchId": "472351",
        }

        get_num = 100
        got_num = 0

        data_params = _build_data_params(mode, url, user_id, get_num, got_num)
        data = {**base_data, **data_params}

        # 开始获取数据
        ctx.log("📥 开始获取数据...")
        all_fav_info = []
        real_got_num = 0

        while True:
            ctx.check_cancel()
            ctx.log(f"   请求 {got_num}-{got_num + get_num}...")
            ctx.set_progress(min(30, int(got_num / 10)))

            response = session.post(requests_url, data=data)
            content = response.content.decode("utf-8")

            # 按 activityTags 切分
            new_info = content.split("activityTags")[1:]
            all_fav_info += new_info
            got_num += get_num
            real_got_num += len(new_info)

            ctx.log(f"   实际返回 {len(new_info)} 条")

            if len(new_info) == 0:
                ctx.log("   已到达最后一页")
                break

            if got_num >= 500:  # 限制获取数量，避免太慢
                ctx.log("   已达到500条限制")
                break

            # 更新请求参数
            if mode in ["like1", "share"]:
                data["c0-param1"] = "number:" + str(get_num)
                data["c0-param2"] = "number:" + str(got_num)
            elif mode == "like2":
                data["c0-param0"] = "number:" + str(get_num)
                data["c0-param1"] = "number:" + str(got_num)
            elif mode == "tag":
                try:
                    last_info = new_info[-1]
                    last_timestamp = re.search(r"s\d{1,5}.publishTime=(.*?);", last_info).group(1)
                    data["c0-param6"] = "number:" + str(get_num)
                    data["c0-param7"] = "number:" + str(got_num)
                    data["c0-param8"] = "number:" + str(last_timestamp)
                except Exception:
                    break

            time.sleep(0.5)

        ctx.log(f"📊 共获取到 {real_got_num} 条博客信息")

        if real_got_num == 0:
            ctx.log("⚠️ 没有获取到任何数据，请检查登录信息和链接")
            return

        # 解析博客信息
        ctx.log("🔄 正在解析博客信息...")
        blogs_info = []
        for fav_info in all_fav_info:
            blog = parse_fav_info(fav_info)
            if blog is not None:
                blogs_info.append(blog)

        ctx.log(f"✅ 解析完成，共 {len(blogs_info)} 条有效博客")

        # 保存内容
        img_count = sum(1 for b in blogs_info if b["has_img"])
        txt_count = sum(1 for b in blogs_info if not b["has_img"])
        ctx.log(f"📊 图片博客: {img_count} 篇, 文字博客: {txt_count} 篇")

        # 创建保存目录 - 按作者分类
        save_root = ctx.config.get("save_path", "./dir")
        base_dir = os.path.join(save_root, f"{mode}_save")
        img_base_dir = os.path.join(base_dir, "img")
        txt_base_dir = os.path.join(base_dir, "txt")
        os.makedirs(img_base_dir, exist_ok=True)
        os.makedirs(txt_base_dir, exist_ok=True)

        saved_img = 0
        saved_txt = 0

        for idx, blog in enumerate(blogs_info):
            ctx.check_cancel()
            ctx.set_progress(30 + int((idx / len(blogs_info)) * 70))

            try:
                # 生成作者目录名
                author_safe = sanitize_filename(blog["author_name"])
                author_folder = f"{author_safe}[{blog['author_ip']}]"
                author_img_dir = os.path.join(img_base_dir, author_folder)

                # 保存图片 - 按作者分类
                if blog["has_img"] and save_mode.get("img"):
                    # 创建作者专属图片目录
                    os.makedirs(author_img_dir, exist_ok=True)

                    for img_idx, img_url in enumerate(blog["img_urls"]):
                        ctx.check_cancel()
                        try:
                            # 确定图片类型
                            img_type = "gif" if "gif" in img_url else ("png" if "png" in img_url else "jpg")

                            pic_name = f"{blog['public_time']}({img_idx + 1}).{img_type}"
                            img_path = os.path.join(author_img_dir, pic_name)

                            req_headers = get_headers()
                            req_headers["Referer"] = blog["url"].split("post")[0]

                            img_content = requests.get(img_url, headers=req_headers, timeout=30).content
                            with open(img_path, "wb") as f:
                                f.write(img_content)

                            saved_img += 1
                        except Exception:
                            continue

                # 保存文章/文本 - 按作者分类
                if (blog["title"] and save_mode.get("article")) or (not blog["title"] and save_mode.get("text")):
                    # 创建作者专属文章目录
                    author_txt_dir = os.path.join(txt_base_dir, author_folder)
                    os.makedirs(author_txt_dir, exist_ok=True)

                    if blog["title"]:
                        title_safe = sanitize_filename(blog["title"])
                        file_name = f"{title_safe}.txt"
                    else:
                        file_name = f"{blog['public_time']}.txt"

                    txt_path = os.path.join(author_txt_dir, file_name)

                    # 避免文件名重复
                    counter = 1
                    original_path = txt_path
                    while os.path.exists(txt_path):
                        name_part = original_path.rsplit(".", 1)[0]
                        txt_path = f"{name_part}({counter}).txt"
                        counter += 1

                    article_head = f"{blog['title'] or '无标题'} by {blog['author_name']}[{blog['author_ip']}]\n"
                    article_head += f"发表时间：{blog['public_time']}\n原文链接：{blog['url']}\n"
                    article_head += "=" * 50 + "\n\n"

                    article = article_head + blog["content"]

                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(article)

                    # 如果需要生成PDF
                    if export_pdf:
                        pdf_path = txt_path.replace(".txt", ".pdf")
                        generate_lofter_pdf(
                            title=blog["title"] or "无标题",
                            author=blog["author_name"],
                            author_ip=blog["author_ip"],
                            public_time=blog["public_time"],
                            url=blog["url"],
                            content=blog["content"],
                            pdf_path=pdf_path,
                        )

                    saved_txt += 1
                    ctx.add_history(
                        "article", blog["url"], blog["title"] or "无标题", blog["author_name"], txt_path, "lofter"
                    )

                # 记录图片博客到历史（仅当没有文章记录时）
                if (
                    blog["has_img"]
                    and save_mode.get("img")
                    and not (
                        (blog["title"] and save_mode.get("article")) or (not blog["title"] and save_mode.get("text"))
                    )
                ):
                    ctx.add_history(
                        "image",
                        blog["url"],
                        f"{blog['author_name']} {len(blog['img_urls'])}张图片",
                        blog["author_name"],
                        author_img_dir,
                        "lofter",
                    )

                if idx % 20 == 0:
                    ctx.log(f"   进度: {idx + 1}/{len(blogs_info)}, 已保存图片 {saved_img} 张, 文章 {saved_txt} 篇")

            except Exception:
                continue

            time.sleep(0.1)

        ctx.log("✅ 保存完成！（文件按作者分类存放）")
        ctx.log(f"   📷 图片: {saved_img} 张 → {img_base_dir}/作者名/")
        ctx.log(f"   📝 文章: {saved_txt} 篇 → {txt_base_dir}/作者名/")

    except Exception as e:
        import traceback

        ctx.log(f"❌ 爬取失败: {str(e)}")
        ctx.log(traceback.format_exc())
