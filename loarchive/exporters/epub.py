"""EPUB 电子书生成（ebooklib）。"""

import os
import uuid

from ..logsetup import get_logger

logger = get_logger("exporter.epub")


def generate_epub(title, author, content_parts, chapters_info, metadata_list, filepath, log=None):
    """生成 EPUB 电子书，成功返回 True。"""
    log = log or (lambda message: logger.info(message))
    try:
        from ebooklib import epub

        book = epub.EpubBook()

        # 设置元数据
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(title)
        book.set_language("zh")
        book.add_author(author)

        # 添加 CSS 样式
        style = """
        body { font-family: "Noto Serif SC", "Source Han Serif", serif; line-height: 1.8; margin: 2em; }
        h1 { text-align: center; margin-bottom: 1em; }
        h2 { border-bottom: 1px solid #ccc; padding-bottom: 0.5em; margin-top: 2em; }
        p { text-indent: 2em; margin-bottom: 0.5em; }
        .meta { font-size: 0.9em; color: #666; margin-bottom: 2em; padding: 1em; background: #f5f5f5; border-radius: 5px; }
        .meta-item { margin-bottom: 0.3em; }
        """
        css = epub.EpubItem(uid="style", file_name="style/main.css", media_type="text/css", content=style)
        book.add_item(css)

        chapters = []

        # 封面/元数据页
        if metadata_list:
            cover_content = '<html><head><link rel="stylesheet" href="style/main.css"/></head><body>'
            cover_content += f"<h1>{title}</h1>"
            cover_content += f'<p style="text-align:center;">by {author}</p>'
            cover_content += '<div class="meta">'
            for meta in metadata_list:
                if meta.strip():
                    cover_content += f'<div class="meta-item">{meta}</div>'
            cover_content += "</div></body></html>"

            cover_chapter = epub.EpubHtml(title="作品信息", file_name="cover.xhtml", lang="zh")
            cover_chapter.content = cover_content
            cover_chapter.add_item(css)
            book.add_item(cover_chapter)
            chapters.append(cover_chapter)

        # 内容章节
        if chapters_info:
            for idx, (ch_title, ch_content) in enumerate(chapters_info):
                ch = epub.EpubHtml(title=ch_title, file_name=f"chapter_{idx + 1}.xhtml", lang="zh")
                content = '<html><head><link rel="stylesheet" href="style/main.css"/></head><body>'
                content += f"<h2>{ch_title}</h2>"
                for para in ch_content:
                    if para.strip():
                        content += f"<p>{para}</p>"
                content += "</body></html>"
                ch.content = content
                ch.add_item(css)
                book.add_item(ch)
                chapters.append(ch)
        else:
            # 单章节
            main_ch = epub.EpubHtml(title="正文", file_name="content.xhtml", lang="zh")
            content = '<html><head><link rel="stylesheet" href="style/main.css"/></head><body>'
            content += f"<h1>{title}</h1>"
            for para in content_parts:
                if para.strip() and not para.strip().startswith("=" * 10):
                    content += f"<p>{para}</p>"
            content += "</body></html>"
            main_ch.content = content
            main_ch.add_item(css)
            book.add_item(main_ch)
            chapters.append(main_ch)

        # 目录
        book.toc = chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav"] + chapters

        # 保存。ebooklib 当前版本会吞掉写入异常，因此这里显式校验产物是否落盘，
        # 避免上层的“已生成 EPUB”日志与实际结果不符。
        epub.write_epub(filepath, book)
        if not os.path.exists(filepath):
            log(f"EPUB生成失败: 文件未写入 {filepath}")
            return False
        return True
    except Exception as e:
        log(f"EPUB生成失败: {e}")
        return False
