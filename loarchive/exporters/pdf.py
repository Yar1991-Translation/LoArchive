"""PDF 生成（xhtml2pdf + reportlab 中文字体）与 AO3 书籍风 HTML 模板。"""

import datetime


def _register_chinese_font() -> None:
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont

        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception:
        pass


def generate_lofter_pdf(title, author, author_ip, public_time, url, content, pdf_path) -> bool:
    """为 Lofter 文章生成 PDF，成功返回 True。"""
    try:
        from xhtml2pdf import pisa

        _register_chinese_font()

        # 处理内容中的换行
        content_html = content.replace("\n", "<br/>")
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title} - {author}</title>
    <style>
        @page {{
            size: A4;
            margin: 2.5cm 2cm;
        }}

        body {{ font-family: STSong-Light, SimSun, serif; font-size: 12pt; line-height: 1.8; color: #333; }}

        /* 封面样式 */
        .cover {{
            text-align: center;
            padding-top: 20%;
            page-break-after: always;
            height: 100%;
        }}

        .cover-title {{
            font-size: 28pt;
            font-weight: bold;
            margin-bottom: 30px;
            color: #2c3e50;
        }}

        .cover-author {{
            font-size: 16pt;
            margin-bottom: 60px;
            color: #555;
        }}

        .cover-meta {{
            font-size: 11pt;
            color: #7f8c8d;
            margin-top: 100px;
            border-top: 1px solid #ddd;
            padding-top: 30px;
            width: 60%;
            margin-left: auto;
            margin-right: auto;
        }}

        /* 正文内容 */
        .content-title {{
            font-size: 18pt;
            font-weight: bold;
            text-align: center;
            margin-bottom: 10px;
            padding-top: 30px;
        }}

        .content-meta {{
            font-size: 10pt;
            color: #999;
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }}

        .content {{ text-align: justify; }}
        .content p {{ text-indent: 2em; margin-bottom: 10px; }}

        a {{ color: #3498db; text-decoration: none; }}
    </style>
</head>
<body>
    <!-- 封面 -->
    <div class="cover">
        <div class="cover-title">{title or "无标题"}</div>
        <div class="cover-author">By {author}</div>

        <div class="cover-meta">
            <div>Published: {public_time}</div>
            <div>Source: Lofter</div>
            <div style="margin-top: 20px; font-size: 10pt;">
                Generated on {current_date}
            </div>
        </div>
    </div>

    <!-- 正文 -->
    <div class="content-title">{title or "无标题"}</div>
    <div class="content-meta">
        作者: {author} [{author_ip}] &nbsp;|&nbsp; 时间: {public_time}<br/>
        原文: {url}
    </div>

    <div class="content">
        <p>{content_html}</p>
    </div>
</body>
</html>"""

        with open(pdf_path, "wb") as pdf_file:
            pisa.CreatePDF(html_content.encode("utf-8"), dest=pdf_file, encoding="utf-8")
        return True
    except Exception:
        return False


def save_ao3_pdf(html_content, filepath, log=print) -> bool:
    """将 HTML 内容保存为 PDF - 使用 xhtml2pdf，支持中文。"""
    try:
        from xhtml2pdf import pisa

        _register_chinese_font()

        with open(filepath, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content.encode("utf-8"), dest=pdf_file, encoding="utf-8")

        if pisa_status.err:
            log("   ⚠️ PDF生成有警告，但文件已创建")
        return True

    except Exception as e:
        log(f"   ⚠️ PDF生成失败: {str(e)}")
        return False


def build_ao3_html(title, author, work_url, metadata_list, content_parts, chapters_info=None) -> str:
    """生成美化的 AO3 HTML 内容 - 书籍风格（用于 PDF 导出与 HTML 落盘）。"""
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # 处理元数据
    meta_html = ""
    fandom = ""
    rating = ""

    if metadata_list:
        for meta in metadata_list:
            meta = meta.strip()
            if not meta:
                continue

            # 提取关键信息用于封面
            if meta.startswith("Fandom:"):
                fandom = meta.split(":", 1)[1].strip()
            elif meta.startswith("Rating:"):
                rating = meta.split(":", 1)[1].strip()

            if ":" in meta:
                key, value = meta.split(":", 1)
                meta_html += f'<div class="meta-item"><span class="meta-label">{key.strip()}:</span> <span class="meta-value">{value.strip()}</span></div>\n'
            else:
                meta_html += f'<div class="meta-item">{meta}</div>\n'

    # 处理正文内容
    content_html = ""
    if chapters_info:
        # 多章节
        for i, (ch_title, ch_content) in enumerate(chapters_info):
            content_html += '<div class="chapter">\n'
            content_html += f'<h2 class="chapter-title">{ch_title}</h2>\n'
            for para in ch_content:
                if para.strip():
                    content_html += f"<p>{para}</p>\n"
            content_html += "</div>\n"
            # 章节结束后添加分页符（除最后一章外）
            if i < len(chapters_info) - 1:
                content_html += '<div class="page-break"></div>\n'
    else:
        # 单章节
        content_html += '<div class="chapter">\n'
        for para in content_parts:
            # 过滤掉TXT格式的分隔符
            if para.strip() and not para.strip().startswith("=" * 10):
                content_html += f"<p>{para}</p>\n"
        content_html += "</div>\n"

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title} - {author}</title>
    <style>
        @page {{
            size: A4;
            margin: 2.5cm 2cm;
        }}

        body {{
            font-family: STSong-Light, SimSun, serif;
            font-size: 12pt;
            line-height: 1.8;
            color: #222;
            background: #fff;
        }}

        /* 封面样式 */
        .cover {{
            text-align: center;
            padding-top: 15%;
            page-break-after: always;
            height: 100%;
        }}

        .cover-title {{
            font-size: 32pt;
            font-weight: bold;
            margin-bottom: 30px;
            color: #2c3e50;
            line-height: 1.3;
        }}

        .cover-author {{
            font-size: 18pt;
            margin-bottom: 60px;
            color: #555;
        }}

        .cover-meta {{
            font-size: 12pt;
            color: #7f8c8d;
            margin-top: 100px;
            border-top: 1px solid #ddd;
            padding-top: 30px;
            width: 60%;
            margin-left: auto;
            margin-right: auto;
        }}

        .cover-fandom {{
            font-style: italic;
            margin-bottom: 10px;
        }}

        /* 元数据页 */
        .metadata-page {{
            page-break-after: always;
            padding: 2cm 0;
        }}

        .metadata-title {{
            font-size: 18pt;
            border-bottom: 2px solid #8B4513;
            padding-bottom: 10px;
            margin-bottom: 30px;
            color: #8B4513;
        }}

        .metadata-content {{
            background-color: #fafafa;
            padding: 20px;
            border: 1px solid #eee;
            border-radius: 5px;
        }}

        .meta-item {{
            margin-bottom: 8px;
            font-size: 11pt;
        }}

        .meta-label {{
            font-weight: bold;
            color: #555;
        }}

        /* 正文样式 */
        .content {{
            text-align: justify;
        }}

        .chapter-title {{
            font-size: 18pt;
            font-weight: bold;
            text-align: center;
            margin: 40px 0 30px 0;
            color: #2c3e50;
        }}

        p {{
            text-indent: 2em;
            margin-bottom: 12px;
            line-height: 1.8;
        }}

        .page-break {{
            page-break-after: always;
        }}

        a {{ color: #3498db; text-decoration: none; }}
    </style>
</head>
<body>
    <!-- 封面页 -->
    <div class="cover">
        <div class="cover-title">{title}</div>
        <div class="cover-author">By {author}</div>

        <div class="cover-meta">
            {f'<div class="cover-fandom">{fandom}</div>' if fandom else ""}
            <div>Rating: {rating or "Not Rated"}</div>
            <div style="margin-top: 20px; font-size: 10pt;">
                Generated by Lofter Spider<br/>
                {current_date}
            </div>
        </div>
    </div>

    <!-- 元数据页 -->
    <div class="metadata-page">
        <div class="metadata-title">Work Details</div>
        <div class="metadata-content">
            {meta_html}
            <div class="meta-item" style="margin-top: 20px; border-top: 1px dashed #ccc; padding-top: 10px;">
                <span class="meta-label">Original URL:</span>
                <span class="meta-value">{work_url}</span>
            </div>
        </div>
    </div>

    <!-- 正文内容 -->
    <div class="content">
        {content_html}
    </div>
</body>
</html>"""
    return html_template
