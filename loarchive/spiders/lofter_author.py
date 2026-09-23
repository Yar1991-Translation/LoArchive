"""Lofter 作者内容爬取：作者图片 / 作者文章。"""

import logging
import os
import re
import time

import requests
from lxml.html import etree

from ..utils import CHROME_UA, filter_lofter_image_urls, get_headers, guess_image_type, sanitize_filename
from .common import LOFTER_IMG_PATTERN, download_file, save_root, unique_file_path
from .lofter_single import extract_article_text, extract_title

logger = logging.getLogger("loarchive.spider.author")

ARCHIVE_QUERY_NUM = 50


def fetch_author_info(author_url: str, cookies: dict):
    """获取作者信息，返回 (author_id, author_name, author_ip)；失败返回 None。"""
    author_view_url = author_url + "view"
    author_view_html = requests.get(author_view_url, headers=get_headers(), cookies=cookies).content.decode("utf-8")
    author_page_parse = etree.HTML(author_view_html)

    try:
        author_id = author_page_parse.xpath("//body//iframe[@id='control_frame']/@src")[0].split("blogId=")[1]
        author_name = author_page_parse.xpath("//title//text()")[0]
        author_ip = re.search(r"http[s]*://(.*).lofter.com/", author_url).group(1)
        return author_id, author_name, author_ip
    except Exception as e:
        logger.warning("从作者主页提取信息失败 %s: %s", author_url, e)
        return None


def fetch_archive_records(
    author_url: str, author_id: str, cookies: dict, ctx, query_num: int = ARCHIVE_QUERY_NUM
) -> list:
    """通过 ArchiveBean DWR 接口分页获取作者全部博客记录（原始字符串列表）。"""
    archive_url = author_url + "dwr/call/plaincall/ArchiveBean.getArchivePostByTime.dwr"

    data = {
        "callCount": "1",
        "scriptSessionId": "${scriptSessionId}187",
        "c0-scriptName": "ArchiveBean",
        "c0-methodName": "getArchivePostByTime",
        "c0-id": "0",
        "c0-param0": f"string:{author_id}",
        "c0-param1": "string:",
        "c0-param2": "number:0",
        "c0-param3": f"number:{query_num}",
        "batchId": "0",
    }
    header = {
        "User-Agent": CHROME_UA,
        "Content-Type": "text/plain",
        "Referer": author_url,
        "Host": "www.lofter.com",
    }

    all_blog_info = []
    page_num = 0

    while True:
        ctx.check_cancel()
        page_num += 1
        ctx.log(f"   获取第 {page_num} 页...")
        ctx.set_progress(min(30, page_num * 5))

        response = requests.post(archive_url, data=data, headers=header, cookies=cookies)
        page_data = response.content.decode("utf-8")

        new_blogs_info = re.findall(r"s[\d]*.blogId.*\n.*noticeLinkTitle", page_data)
        all_blog_info += new_blogs_info

        if len(new_blogs_info) < query_num:
            break

        try:
            data["c0-param2"] = "number:" + str(re.search(rf"s{query_num - 1}\.time=(.*);s.*type", page_data).group(1))
        except Exception:
            # 拿不到下一页游标，视为翻页结束
            logger.debug("归档页未找到下一页时间戳，停止翻页")
            break

        time.sleep(0.5)

    return all_blog_info


def parse_archive_records(all_blog_info: list) -> list:
    """解析归档记录（纯函数），返回 [{permalink, time, has_img}, ...]。"""
    records = []
    for blog_info in all_blog_info:
        try:
            img_url_match = re.findall(r'[\d]*.imgurl="(.*?)"', blog_info)
            # 非贪婪匹配：原实现用 (.*) 依赖 permalink 是记录最后一个字段，
            # 字段顺序变化时会吞掉后续内容，此处收紧为 (.*?)
            blog_index = re.search(r's[\d]*.permalink="(.*?)"', blog_info).group(1)
            timestamp = re.search(r"s[\d]*.time=(\d*);", blog_info).group(1)
            dt_time = time.strftime("%Y-%m-%d", time.localtime(int(int(timestamp) / 1000)))
            records.append(
                {
                    "permalink": blog_index,
                    "time": dt_time,
                    "has_img": bool(img_url_match),
                }
            )
        except Exception:
            # 单条记录缺字段时跳过（列表页的尾部碎片等）
            logger.debug("跳过无法解析的归档记录: %s", blog_info[:80])
            continue
    return records


def run_author_img(ctx, params: dict) -> None:
    """运行作者图片爬取任务。"""
    ctx.log("🚀 开始爬取作者图片")
    author_url = params.get("author_url", "")

    if not author_url:
        ctx.log("❌ 请提供作者主页链接")
        return

    if not author_url.endswith("/"):
        author_url += "/"

    ctx.log(f"📍 作者主页: {author_url}")

    try:
        login_key = ctx.config["login_key"]
        login_auth = ctx.config["login_auth"]
        cookies = {login_key: login_auth}

        # 获取作者信息
        info = fetch_author_info(author_url, cookies)
        if info is None:
            ctx.log("❌ 无法获取作者信息")
            return
        author_id, author_name, author_ip = info
        ctx.log(f"👤 作者: {author_name} ({author_ip})")

        # 获取归档页
        ctx.log("📚 正在获取归档页...")
        all_blog_info = fetch_archive_records(author_url, author_id, cookies, ctx)

        ctx.log(f"📊 共获取 {len(all_blog_info)} 条博客记录")

        # 解析博客信息，获取图片博客
        records = parse_archive_records(all_blog_info)
        img_blogs = [{"url": author_url + "post/" + r["permalink"], "time": r["time"]} for r in records if r["has_img"]]

        ctx.log(f"🖼️ 共找到 {len(img_blogs)} 篇图片博客")

        if not img_blogs:
            ctx.log("⚠️ 没有找到图片博客")
            return

        # 创建保存目录
        author_name_safe = sanitize_filename(author_name)
        dir_path = os.path.join(save_root(ctx), f"img/{author_name_safe}[{author_ip}]")
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # 下载图片
        total_saved = 0
        for idx, blog in enumerate(img_blogs):
            ctx.check_cancel()
            ctx.set_progress(30 + int((idx / len(img_blogs)) * 70))

            try:
                blog_html = requests.get(blog["url"], headers=get_headers(), cookies=cookies).content.decode("utf-8")

                imgs_url = re.findall(LOFTER_IMG_PATTERN, blog_html)

                # 过滤
                filtered_imgs = filter_lofter_image_urls(imgs_url)

                for img_idx, img_url in enumerate(filtered_imgs):
                    ctx.check_cancel()
                    img_type = guess_image_type(img_url)

                    pic_name = f"{author_name_safe}[{author_ip}] {blog['time']}({img_idx + 1}).{img_type}"
                    img_path = os.path.join(dir_path, pic_name)

                    download_file(img_url, img_path, referer=author_url)

                    total_saved += 1

                if idx % 10 == 0:
                    ctx.log(f"   📥 进度: {idx + 1}/{len(img_blogs)} 博客, 已保存 {total_saved} 张图片")

            except Exception as e:
                logger.warning("处理博客失败 %s: %s", blog["url"], e)
                ctx.log(f"   ⚠️ 处理博客失败: {blog['url']} - {str(e)}")
                continue

            time.sleep(0.3)

        # 记录到下载历史
        if total_saved > 0:
            ctx.add_history("image", author_url, f"{author_name} {total_saved}张图片", author_name, dir_path, "lofter")

        ctx.log(f"✅ 完成！共保存 {total_saved} 张图片到 {dir_path}")

    except Exception as e:
        logger.exception("作者图片任务执行失败")
        import traceback

        ctx.log(f"❌ 爬取失败: {str(e)}")
        ctx.log(traceback.format_exc())


def run_author_txt(ctx, params: dict) -> None:
    """运行作者文章爬取任务（复用归档列表 + 单篇文章提取逻辑）。"""
    ctx.log("🚀 开始爬取作者文章")
    author_url = params.get("author_url", "")

    if not author_url:
        ctx.log("❌ 请提供作者主页链接")
        return

    if not author_url.endswith("/"):
        author_url += "/"

    ctx.log(f"📍 作者主页: {author_url}")

    try:
        login_key = ctx.config["login_key"]
        login_auth = ctx.config["login_auth"]
        cookies = {login_key: login_auth}

        # 获取作者信息
        info = fetch_author_info(author_url, cookies)
        if info is None:
            ctx.log("❌ 无法获取作者信息")
            return
        author_id, author_name, author_ip = info
        ctx.log(f"👤 作者: {author_name} ({author_ip})")

        # 获取归档页
        ctx.log("📚 正在获取归档页...")
        all_blog_info = fetch_archive_records(author_url, author_id, cookies, ctx)
        records = parse_archive_records(all_blog_info)

        ctx.log(f"📊 共获取 {len(records)} 条博客记录")

        if not records:
            ctx.log("⚠️ 没有找到任何博客")
            return

        # 创建保存目录
        author_name_safe = sanitize_filename(author_name)
        dir_path = os.path.join(save_root(ctx), f"article/{author_name_safe}[{author_ip}]")
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        saved_count = 0
        skipped_count = 0

        for idx, record in enumerate(records):
            ctx.check_cancel()
            ctx.set_progress(30 + int((idx / len(records)) * 70))

            blog_url = author_url + "post/" + record["permalink"]

            try:
                blog_html = requests.get(blog_url, headers=get_headers(), cookies=cookies).content.decode("utf-8")
                blog_parse = etree.HTML(blog_html)

                title = extract_title(blog_parse)
                # 仅使用正文区域提取（不回退整页转换），纯图片博客无正文则跳过
                content_text = extract_article_text(blog_parse, blog_html, allow_full_fallback=False)

                if not content_text.strip():
                    skipped_count += 1
                    continue

                # 构建文章
                article_head = (
                    f"{title if title else '无标题'} by {author_name}[{author_ip}]\n"
                    f"发表时间：{record['time']}\n原文链接：{blog_url}"
                )
                article = article_head + "\n\n" + "=" * 50 + "\n\n" + content_text

                # 生成文件名
                if title:
                    file_name = f"{title} by {author_name}.txt"
                else:
                    file_name = f"{author_name} {record['time']}.txt"
                file_name = sanitize_filename(file_name)

                file_path = unique_file_path(dir_path, file_name)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(article)

                saved_count += 1
                ctx.log(f"   💾 [{idx + 1}/{len(records)}] 已保存: {os.path.basename(file_path)}")
                ctx.add_history(
                    "article", blog_url, title or f"{author_name} {record['time']}", author_name, file_path, "lofter"
                )

            except Exception as e:
                logger.warning("解析博客失败 %s: %s", blog_url, e)
                ctx.log(f"   ⚠️ 解析失败: {blog_url} - {str(e)}")
                continue

            time.sleep(0.5)  # 防止请求过快

        if saved_count > 0:
            ctx.add_history(
                "article", author_url, f"{author_name} {saved_count}篇文章", author_name, dir_path, "lofter"
            )

        ctx.log(f"✅ 文章保存完成！共保存 {saved_count} 篇（跳过无正文博客 {skipped_count} 篇）到 {dir_path}")

    except Exception as e:
        logger.exception("作者文章任务执行失败")
        import traceback

        ctx.log(f"❌ 爬取失败: {str(e)}")
        ctx.log(traceback.format_exc())
