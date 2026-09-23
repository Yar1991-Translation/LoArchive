"""AO3 文章爬取 - 参考 https://github.com/610yilingliu/download_ao3_v2"""

import logging
import os
import re
import time

import requests
from bs4 import BeautifulSoup
from lxml import etree

from ..exporters.epub import generate_epub
from ..exporters.pdf import build_ao3_html, save_ao3_pdf
from ..utils import sanitize_filename
from .common import save_root, unique_file_path

logger = logging.getLogger("loarchive.spider.ao3")

AO3_BASE = "https://archiveofourown.org"


def safe_filename(name: str) -> str:
    """生成安全的文件名（纯函数）：字符映射清洗 + 空白折叠 + 截断到 100 字符。"""
    name = sanitize_filename(name)
    # 移除连续空格和下划线
    name = re.sub(r"[_\s]+", " ", name).strip()
    return name[:100] if name else "untitled"


def build_session() -> requests.Session:
    """AO3 请求 Session - 更好的连接管理。"""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    )
    # 设置cookie绕过年龄确认
    session.cookies.set("accepted_tos", "20180523", domain=".archiveofourown.org")
    session.cookies.set("view_adult", "true", domain=".archiveofourown.org")
    return session


def fetch_with_retry(ctx, session: requests.Session, url: str, max_retries: int = 3, wait_time: int = 30):
    """带重试逻辑的请求函数。"""
    for attempt in range(max_retries):
        ctx.check_cancel()
        try:
            response = session.get(url, timeout=30)

            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                # 请求过于频繁
                ctx.log(f"   ⚠️ 请求过于频繁(429)，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue
            elif response.status_code == 404:
                ctx.log("   ⚠️ 作品不存在或已删除 (404)")
                return None
            elif response.status_code == 403:
                ctx.log("   ⚠️ 无权访问 (403)，可能需要登录或作品已锁定")
                return None
            else:
                ctx.log(f"   ⚠️ HTTP {response.status_code}，重试中...")
                time.sleep(5)

        except requests.exceptions.Timeout:
            ctx.log(f"   ⚠️ 请求超时，重试 {attempt + 1}/{max_retries}")
            time.sleep(10)
        except requests.exceptions.ConnectionError:
            ctx.log(f"   ⚠️ 连接错误，重试 {attempt + 1}/{max_retries}")
            time.sleep(10)
        except Exception as e:
            ctx.log(f"   ⚠️ 请求错误: {str(e)}")
            time.sleep(5)

    ctx.log("   ❌ 多次重试后仍然失败")
    return None


def extract_work_metadata(tree, save_metadata: bool = True) -> list:
    """从作品页面提取元数据列表（纯函数）。"""
    metadata = []
    if not save_metadata:
        return metadata

    # Fandom
    fandoms = tree.xpath('//dd[@class="fandom tags"]//a/text()')
    if fandoms:
        metadata.append(f"Fandom: {', '.join(fandoms)}")

    # Rating
    rating = tree.xpath('//dd[@class="rating tags"]//a/text()')
    if rating:
        metadata.append(f"Rating: {rating[0]}")

    # Warnings
    warnings = tree.xpath('//dd[@class="warning tags"]//a/text()')
    if warnings:
        metadata.append(f"Warnings: {', '.join(warnings)}")

    # Relationships
    relationships = tree.xpath('//dd[@class="relationship tags"]//a/text()')
    if relationships:
        metadata.append(f"Relationships: {', '.join(relationships[:5])}")

    # Characters
    characters = tree.xpath('//dd[@class="character tags"]//a/text()')
    if characters:
        metadata.append(f"Characters: {', '.join(characters[:10])}")

    # Additional Tags
    tags = tree.xpath('//dd[@class="freeform tags"]//a/text()')
    if tags:
        metadata.append(f"Tags: {', '.join(tags[:10])}")

    # Summary
    summary_elem = tree.xpath('//div[@class="summary module"]//blockquote//text()')
    if summary_elem:
        summary = " ".join([s.strip() for s in summary_elem if s.strip()])
        metadata.append(f"\nSummary:\n{summary}")

    # Stats
    words = tree.xpath('//dd[@class="words"]/text()')
    chapters = tree.xpath('//dd[@class="chapters"]/text()')
    if words:
        metadata.append(f"\nWords: {words[0]}")
    if chapters:
        metadata.append(f"Chapters: {chapters[0]}")

    return metadata


def extract_work_title_author(html_content: str):
    """提取作品标题与作者（纯函数）。"""
    soup = BeautifulSoup(html_content, "html.parser")

    title_elem = soup.find("h2", class_="title heading")
    title = title_elem.get_text(strip=True) if title_elem else "未知标题"

    author_elem = soup.find("a", rel="author")
    author = author_elem.get_text(strip=True) if author_elem else "未知作者"

    return title, author


def extract_page_content(tree) -> list:
    """从作品页面提取单章正文段落（纯函数，带回退）。"""
    content_parts = []
    content_elem = tree.xpath('//div[@class="userstuff module"]//p | //div[@id="chapters"]//div[@class="userstuff"]//p')
    for p in content_elem:
        text = etree.tostring(p, method="text", encoding="unicode")
        if text.strip():
            content_parts.append(text.strip())

    if not content_parts:
        # 尝试其他方式获取内容
        content_elem = tree.xpath('//div[contains(@class, "userstuff")]//text()')
        content_parts = [t.strip() for t in content_elem if t.strip() and len(t.strip()) > 10]

    return content_parts


def extract_chapter(ch_tree, idx: int):
    """提取章节标题与正文（纯函数），返回 (ch_title, ch_content)。"""
    ch_title_elem = ch_tree.xpath('//h3[@class="title"]//text()')
    ch_title = " ".join([t.strip() for t in ch_title_elem if t.strip()])
    if not ch_title:
        ch_title = f"第 {idx + 1} 章"

    ch_content_elem = ch_tree.xpath('//div[@class="userstuff module"]//p')
    ch_content = []
    for p in ch_content_elem:
        text = etree.tostring(p, method="text", encoding="unicode")
        if text.strip():
            ch_content.append(text.strip())

    return ch_title, ch_content


def download_work(ctx, session: requests.Session, base_dir: str, work_url: str, params: dict) -> bool:
    """下载单个作品，成功保存返回 True。"""
    download_chapters = params.get("download_chapters", True)
    save_metadata = params.get("save_metadata", True)
    export_pdf = params.get("export_pdf", False)
    export_epub = params.get("export_epub", False)

    try:
        # 检查是否已下载（自动去重）
        if ctx.is_downloaded(work_url):
            ctx.log(f"⏭️ 已下载过，跳过: {work_url}")
            return False

        ctx.log(f"📖 正在获取: {work_url}")

        # 处理 ?view_adult=true 参数
        if "?" not in work_url:
            work_url_with_adult = work_url + "?view_adult=true"
        else:
            work_url_with_adult = work_url + "&view_adult=true"

        # 获取作品页面 (带重试)
        response = fetch_with_retry(ctx, session, work_url_with_adult)
        if response is None:
            return False

        html_content = response.content.decode("utf-8")
        tree = etree.HTML(html_content)

        # 提取作品信息
        title, author = extract_work_title_author(html_content)

        # 获取元数据
        metadata = extract_work_metadata(tree, save_metadata)

        ctx.log(f"   📝 标题: {title}")
        ctx.log(f"   👤 作者: {author}")

        # 获取正文内容
        content_parts = []
        chapters_info = []  # 用于PDF生成: [(章节标题, [段落列表]), ...]

        # 检查是否有多章节
        chapter_links = tree.xpath('//div[@id="chapter_index"]//option/@value')

        if chapter_links and download_chapters and len(chapter_links) > 1:
            ctx.log(f"   📑 共 {len(chapter_links)} 章节")

            for idx, chapter_id in enumerate(chapter_links):
                ctx.check_cancel()
                chapter_url = f"{work_url.split('?')[0]}/chapters/{chapter_id.split('/')[-1]}?view_adult=true"
                ctx.log(f"      第 {idx + 1}/{len(chapter_links)} 章...")
                ctx.set_progress(int((idx / len(chapter_links)) * 50) + 50)

                try:
                    ch_response = fetch_with_retry(ctx, session, chapter_url)
                    if ch_response is None:
                        continue
                    ch_tree = etree.HTML(ch_response.content.decode("utf-8"))

                    # 章节标题与内容
                    ch_title, ch_content = extract_chapter(ch_tree, idx)

                    # 保存章节信息用于PDF
                    chapters_info.append((ch_title, ch_content))

                    # TXT格式
                    if ch_title:
                        content_parts.append(f"\n\n{'=' * 60}\n{ch_title}\n{'=' * 60}\n")
                    content_parts.append("\n\n".join(ch_content))

                    time.sleep(0.5)  # 避免请求过快

                except Exception as e:
                    ctx.log(f"      ⚠️ 获取章节失败: {str(e)}")
        else:
            # 单章节或不下载全部章节
            content_parts = extract_page_content(tree)

        # 组装TXT文章
        article = f"{title}\nby {author}\n"
        article += f"原文链接: {work_url}\n"
        article += "\n" + "=" * 60 + "\n"

        if metadata:
            article += "\n".join(metadata)
            article += "\n\n" + "=" * 60 + "\n"

        article += "\n\n".join(content_parts)

        # 创建作者目录
        author_dir = os.path.join(base_dir, safe_filename(author))
        os.makedirs(author_dir, exist_ok=True)

        # 保存TXT文件
        txt_filename = f"{safe_filename(title)}.txt"
        txt_filepath = unique_file_path(author_dir, txt_filename)

        with open(txt_filepath, "w", encoding="utf-8") as f:
            f.write(article)

        ctx.log(f"   ✅ 已保存: {txt_filename}")

        # 记录到下载历史
        ctx.add_history(
            item_type="ao3",
            url=work_url,
            title=title,
            author=author,
            file_path=txt_filepath,
            source="ao3",
        )

        # 如果需要导出PDF
        if export_pdf:
            ctx.log("   📄 正在生成PDF...")
            pdf_filename = txt_filename.replace(".txt", ".pdf")
            pdf_filepath = txt_filepath.replace(".txt", ".pdf")

            # 生成HTML内容
            html_for_pdf = build_ao3_html(
                title=title,
                author=author,
                work_url=work_url,
                metadata_list=metadata,
                content_parts=content_parts if not chapters_info else [],
                chapters_info=chapters_info if chapters_info else None,
            )

            # 同时保存HTML文件（方便调试和自定义）
            html_filepath = txt_filepath.replace(".txt", ".html")
            with open(html_filepath, "w", encoding="utf-8") as f:
                f.write(html_for_pdf)

            # 生成PDF
            if save_ao3_pdf(html_for_pdf, pdf_filepath, log=ctx.log):
                ctx.log(f"   📄 已生成PDF: {pdf_filename}")

        # 如果需要导出EPUB
        if export_epub:
            ctx.log("   📖 正在生成EPUB...")
            epub_filename = txt_filename.replace(".txt", ".epub")
            epub_filepath = txt_filepath.replace(".txt", ".epub")

            if generate_epub(
                title=title,
                author=author,
                content_parts=content_parts,
                chapters_info=chapters_info if chapters_info else None,
                metadata_list=metadata,
                filepath=epub_filepath,
            ):
                ctx.log(f"   📖 已生成EPUB: {epub_filename}")

        return True

    except Exception as e:
        logger.exception("下载作品失败 %s", work_url)
        ctx.log(f"   ❌ 下载失败: {str(e)}")
        return False


def get_works_from_series(ctx, session: requests.Session, series_url: str) -> list:
    """获取系列中的所有作品链接。"""
    try:
        ctx.log(f"📚 获取系列作品列表: {series_url}")
        response = fetch_with_retry(ctx, session, series_url)
        if response is None:
            return []
        tree = etree.HTML(response.content.decode("utf-8"))

        work_links = tree.xpath('//ul[@class="series work index group"]//h4[@class="heading"]//a[1]/@href')
        work_urls = [f"{AO3_BASE}{link}" for link in work_links if "/works/" in link]

        ctx.log(f"   找到 {len(work_urls)} 篇作品")
        return work_urls
    except Exception as e:
        ctx.log(f"   ❌ 获取系列失败: {str(e)}")
        return []


def get_works_from_author(ctx, session: requests.Session, author_url: str, max_pages: int = 20) -> list:
    """获取作者的所有作品链接。"""
    try:
        ctx.log(f"👤 获取作者作品列表: {author_url}")

        all_works = []
        page = 1

        while True:
            ctx.check_cancel()
            page_url = f"{author_url}?page={page}"
            response = fetch_with_retry(ctx, session, page_url)
            if response is None:
                break
            tree = etree.HTML(response.content.decode("utf-8"))

            work_links = tree.xpath('//ol[@class="work index group"]//h4[@class="heading"]//a[1]/@href')
            new_works = [f"{AO3_BASE}{link}" for link in work_links if "/works/" in link]

            if not new_works:
                break

            all_works.extend(new_works)
            ctx.log(f"   第 {page} 页: 找到 {len(new_works)} 篇")

            # 检查是否有下一页
            next_page = tree.xpath('//li[@class="next"]//a/@href')
            if not next_page:
                break

            page += 1
            if page > max_pages:
                ctx.log(f"   ⚠️ 已达到 {max_pages} 页限制")
                break

            time.sleep(0.5)

        ctx.log(f"   共找到 {len(all_works)} 篇作品")
        return all_works

    except Exception as e:
        ctx.log(f"   ❌ 获取作者作品失败: {str(e)}")
        return []


def get_works_from_tag(ctx, session: requests.Session, tag_url: str, max_pages: int = 5) -> list:
    """获取Tag下的所有作品链接。"""
    try:
        # 提取tag名称用于显示
        tag_match = re.search(r"/tags/([^/]+)/works", tag_url)
        tag_name = tag_match.group(1) if tag_match else "未知标签"
        tag_name = requests.utils.unquote(tag_name)

        ctx.log(f"🏷️ 获取Tag作品列表: {tag_name}")

        all_works = []
        page = 1

        while True:
            ctx.check_cancel()
            # AO3 tag页面的分页格式
            if "?" in tag_url:
                page_url = f"{tag_url}&page={page}"
            else:
                page_url = f"{tag_url}?page={page}"

            ctx.log(f"   正在获取第 {page} 页...")
            response = fetch_with_retry(ctx, session, page_url)

            if response is None:
                ctx.log("   ⚠️ 获取页面失败")
                break

            tree = etree.HTML(response.content.decode("utf-8"))

            # AO3 作品列表的选择器
            work_links = tree.xpath('//ol[contains(@class, "work index")]//h4[@class="heading"]//a[1]/@href')
            new_works = [f"{AO3_BASE}{link}" for link in work_links if "/works/" in link]

            if not new_works:
                ctx.log(f"   第 {page} 页没有更多作品")
                break

            all_works.extend(new_works)
            ctx.log(f"   第 {page} 页: 找到 {len(new_works)} 篇")

            # 检查是否有下一页
            next_page = tree.xpath('//li[@class="next"]//a/@href')
            if not next_page:
                ctx.log("   已到达最后一页")
                break

            page += 1
            if page > max_pages:
                ctx.log(f"   ⚠️ 已达到 {max_pages} 页限制")
                break

            time.sleep(1)  # AO3对频繁请求比较敏感

        ctx.log(f"   🏷️ Tag [{tag_name}] 共找到 {len(all_works)} 篇作品")
        return all_works

    except Exception as e:
        ctx.log(f"   ❌ 获取Tag作品失败: {str(e)}")
        return []


def run(ctx, params: dict) -> None:
    """运行AO3文章爬取任务。"""
    urls = params.get("urls", [])
    mode = params.get("mode", "work")  # work, series, author, tag

    if not urls:
        ctx.log("❌ 请提供AO3链接")
        return

    ctx.log(f"📚 开始AO3爬取任务，模式: {mode}")
    ctx.log(f"📍 共 {len(urls)} 个链接")

    # 创建保存目录（使用自定义路径）
    base_dir = os.path.join(save_root(ctx), "ao3")
    os.makedirs(base_dir, exist_ok=True)

    session = build_session()

    # 获取最大页数参数
    max_pages = params.get("max_pages", 5)

    # 处理每个URL
    all_work_urls = []

    for url in urls:
        ctx.check_cancel()
        url = url.strip()
        if not url:
            continue

        if "/series/" in url:
            # 系列作品
            work_urls = get_works_from_series(ctx, session, url)
            all_work_urls.extend(work_urls)
        elif "/users/" in url and "/works" in url:
            # 作者作品页
            work_urls = get_works_from_author(ctx, session, url, max_pages)
            all_work_urls.extend(work_urls)
        elif "/tags/" in url and "/works" in url:
            # Tag作品页
            work_urls = get_works_from_tag(ctx, session, url, max_pages)
            all_work_urls.extend(work_urls)
        elif "/works/" in url:
            # 单个作品
            all_work_urls.append(url)
        else:
            ctx.log(f"⚠️ 无法识别的链接格式: {url}")

    # 去重
    all_work_urls = list(dict.fromkeys(all_work_urls))
    ctx.log(f"📊 共 {len(all_work_urls)} 篇作品待下载")

    # 下载所有作品
    saved_count = 0
    for idx, work_url in enumerate(all_work_urls):
        ctx.check_cancel()
        ctx.set_progress(int((idx / len(all_work_urls)) * 100))
        if download_work(ctx, session, base_dir, work_url, params):
            saved_count += 1
        time.sleep(1)  # 避免请求过快

    ctx.log("✅ AO3下载完成！")
    ctx.log(f"   📚 共保存 {saved_count} 篇文章")
    ctx.log(f"   📁 保存位置: {base_dir}/作者名/")
