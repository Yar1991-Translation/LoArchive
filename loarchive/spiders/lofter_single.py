"""Lofter 单篇保存：图片 / 文章。"""

import os
import re
import time

import requests
from lxml.html import etree

from ..utils import filter_lofter_image_urls, get_headers, guess_image_type, sanitize_filename


def extract_public_time(html: str) -> str:
    """从博客页面 HTML 提取发表时间（纯函数）。"""
    re_date = re.search(r"\d{4}[.\\\/-]\d{2}[.\\\/-]\d{2}", html)
    if re_date:
        return re_date.group(0).replace("\\", "-").replace(".", "-").replace("/", "-")
    return time.strftime("%Y-%m-%d")


def find_lofter_images(html: str) -> list:
    """从博客页面 HTML 提取并过滤图片链接（纯函数）。"""
    imgs_url = re.findall(r'"(http[s]{0,1}://imglf\d{0,1}.lf\d*.[0-9]{0,3}.net.*?)"', html)
    return filter_lofter_image_urls(imgs_url)


def extract_article_text(blog_parse, blog_html: str, allow_full_fallback: bool = True) -> str:
    """按三级回退策略提取正文文本（纯函数）。

    allow_full_fallback=False 时不做整页 html2text 转换
    （作者文章批量提取时使用，避免纯图片博客产生整页噪音文本）。
    """
    content_text = ""

    # 方法1: 尝试获取文章主体
    content_elements = blog_parse.xpath("//div[contains(@class,'content')]//text()")
    if content_elements:
        content_text = "\n".join([t.strip() for t in content_elements if t.strip()])

    # 方法2: 如果方法1失败，尝试获取所有p标签
    if not content_text:
        p_elements = blog_parse.xpath("//article//p//text() | //div[@class='text']//p//text()")
        if p_elements:
            content_text = "\n\n".join([t.strip() for t in p_elements if t.strip()])

    # 方法3: 使用html2text转换
    if not content_text and allow_full_fallback:
        import html2text

        try:
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            content_text = h.handle(blog_html)
            # 清理一些无用内容
            content_text = re.sub(r"\n{3,}", "\n\n", content_text)
        except Exception:
            content_text = "无法解析正文内容"

    return content_text


def extract_title(blog_parse) -> str:
    """提取文章标题（纯函数）。"""
    title_path = blog_parse.xpath("//h2//text()")
    if title_path:
        return title_path[0].strip()
    return ""


def fetch_blog_context(blog_url: str, cookies: dict):
    """获取博客页面与作者信息，返回 (blog_html, author_name, author_ip, public_time)。"""
    blog_html = requests.get(blog_url, headers=get_headers(), cookies=cookies).content.decode("utf-8")

    author_view_url = blog_url.split("/post")[0] + "/view"
    author_view_html = requests.get(author_view_url, headers=get_headers(), cookies=cookies).content.decode("utf-8")
    author_view_parse = etree.HTML(author_view_html)

    try:
        author_name = author_view_parse.xpath("//h1/a/text()")[0]
    except Exception:
        author_name = "未知作者"

    author_ip = re.search(r"http(s)*://(.*).lofter.com/", blog_url).group(2)
    public_time = extract_public_time(blog_html)
    return blog_html, author_name, author_ip, public_time


def run_single_img(ctx, params: dict) -> None:
    """运行单篇图片爬取任务。"""
    urls = params.get("urls", [])
    if not urls:
        ctx.log("❌ 没有提供链接")
        return

    ctx.log(f"🚀 开始单篇图片爬取，共 {len(urls)} 个链接")

    login_key = ctx.config["login_key"]
    login_auth = ctx.config["login_auth"]
    cookies = {login_key: login_auth}

    # 确保目录存在
    save_root = ctx.config.get("save_path", "./dir")
    dir_path = os.path.join(save_root, "img/this")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    all_imgs_info = []

    # 解析每个博客
    for idx, blog_url in enumerate(urls):
        ctx.check_cancel()
        blog_url = blog_url.strip()
        if not blog_url:
            continue

        ctx.set_progress(int((idx / len(urls)) * 50))
        ctx.log(f"📖 [{idx + 1}/{len(urls)}] 解析博客: {blog_url}")

        try:
            # 获取博客页面与作者信息
            blog_html, author_name, author_ip, public_time = fetch_blog_context(blog_url, cookies)

            # 匹配并过滤图片链接
            filtered_imgs = find_lofter_images(blog_html)

            ctx.log(f"   找到 {len(filtered_imgs)} 张图片")

            # 整理图片信息
            for img_idx, img_url in enumerate(filtered_imgs):
                img_type = guess_image_type(img_url)
                author_name_safe = sanitize_filename(author_name)

                pic_name = f"{author_name_safe}[{author_ip}] {public_time}({img_idx + 1}).{img_type}"
                all_imgs_info.append(
                    {
                        "img_url": img_url,
                        "pic_name": pic_name,
                        "referer": blog_url.split("post")[0],
                    }
                )

        except Exception as e:
            ctx.log(f"   ⚠️ 解析失败: {str(e)}")
            continue

    ctx.log(f"📷 共获取到 {len(all_imgs_info)} 张图片，开始下载...")

    # 下载图片
    for idx, img_info in enumerate(all_imgs_info):
        ctx.check_cancel()
        ctx.set_progress(50 + int((idx / len(all_imgs_info)) * 50))

        pic_url = img_info["img_url"]
        pic_name = img_info["pic_name"]
        img_path = os.path.join(dir_path, pic_name)

        try:
            headers = get_headers()
            headers["Referer"] = img_info.get("referer", "")

            response = requests.get(pic_url, headers=headers, timeout=30)
            with open(img_path, "wb") as f:
                f.write(response.content)

            ctx.log(f"   💾 [{idx + 1}/{len(all_imgs_info)}] 已保存: {pic_name}")

        except Exception as e:
            ctx.log(f"   ⚠️ 下载失败: {pic_name} - {str(e)}")

        if idx % 5 == 0:
            time.sleep(0.5)  # 防止请求过快

    # 记录到下载历史（按博客URL去重）
    if all_imgs_info:
        ctx.add_history("image", urls[0], f"{len(all_imgs_info)}张图片", "批量下载", dir_path, "lofter")

    ctx.log(f"✅ 图片保存完成！共保存 {len(all_imgs_info)} 张图片到 {dir_path}")


def run_single_txt(ctx, params: dict) -> None:
    """运行单篇文章爬取任务。"""
    urls = params.get("urls", [])
    if not urls:
        ctx.log("❌ 没有提供链接")
        return

    ctx.log(f"🚀 开始单篇文章爬取，共 {len(urls)} 个链接")

    login_key = ctx.config["login_key"]
    login_auth = ctx.config["login_auth"]
    cookies = {login_key: login_auth}

    # 确保目录存在
    save_root = ctx.config.get("save_path", "./dir")
    dir_path = os.path.join(save_root, "article/this")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    saved_count = 0

    for idx, blog_url in enumerate(urls):
        ctx.check_cancel()
        blog_url = blog_url.strip()
        if not blog_url:
            continue

        ctx.set_progress(int((idx / len(urls)) * 100))
        ctx.log(f"📖 [{idx + 1}/{len(urls)}] 解析博客: {blog_url}")

        try:
            # 获取博客页面与作者信息
            blog_html, author_name, author_ip, public_time = fetch_blog_context(blog_url, cookies)
            blog_parse = etree.HTML(blog_html)

            # 获取标题与正文内容
            title = extract_title(blog_parse)
            content_text = extract_article_text(blog_parse, blog_html)

            # 构建文章
            article_head = (
                f"{title if title else '无标题'} by {author_name}[{author_ip}]\n"
                f"发表时间：{public_time}\n原文链接：{blog_url}"
            )
            article = article_head + "\n\n" + "=" * 50 + "\n\n" + content_text

            # 生成文件名
            if title:
                file_name = f"{title} by {author_name}.txt"
            else:
                file_name = f"{author_name} {public_time}.txt"

            # 清理文件名中的非法字符
            file_name = sanitize_filename(file_name)

            # 保存文件
            file_path = os.path.join(dir_path, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(article)

            saved_count += 1
            ctx.log(f"   💾 已保存: {file_name}")
            ctx.add_history(
                "article", blog_url, title or f"{author_name} {public_time}", author_name, file_path, "lofter"
            )

        except Exception as e:
            ctx.log(f"   ⚠️ 保存失败: {str(e)}")
            continue

        time.sleep(0.5)  # 防止请求过快

    ctx.log(f"✅ 文章保存完成！共保存 {saved_count} 篇文章到 {dir_path}")
