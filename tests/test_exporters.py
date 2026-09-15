"""导出器测试：真实落盘 PDF / EPUB，验证文件有效。"""

import zipfile

from loarchive.exporters.epub import generate_epub
from loarchive.exporters.pdf import build_ao3_html, generate_lofter_pdf, save_ao3_pdf


def test_build_ao3_html_includes_metadata_and_chapters():
    html = build_ao3_html(
        title="作品标题",
        author="作者名",
        work_url="https://archiveofourown.org/works/1",
        metadata_list=["Fandom: 测试圈", "Rating: General Audiences"],
        content_parts=[],
        chapters_info=[("第一章", ["甲", "乙"]), ("第二章", ["丙"])],
    )

    assert "作品标题" in html
    assert "作者名" in html
    # 元数据渲染为 label / value 两个 span
    assert ">Fandom:<" in html
    assert ">测试圈<" in html
    assert "第一章" in html
    assert "第二章" in html
    assert 'class="page-break"' in html


def test_build_ao3_html_handles_single_chapter_content():
    html = build_ao3_html(
        title="单章",
        author="作者",
        work_url="https://archiveofourown.org/works/2",
        metadata_list=[],
        content_parts=["第一段", "=" * 20, "第二段"],
    )

    assert "第一段" in html
    assert "第二段" in html
    # TXT 分隔符不应进入 HTML
    assert "====" not in html


def test_generate_ao3_pdf_creates_readable_pdf(tmp_path):
    html = build_ao3_html(
        title="PDF 测试",
        author="作者",
        work_url="https://archiveofourown.org/works/3",
        metadata_list=["Fandom: 测试"],
        content_parts=["中文段落内容"],
    )
    target = tmp_path / "out.pdf"

    assert save_ao3_pdf(html, str(target)) is True
    assert target.exists()
    assert target.stat().st_size > 0
    assert target.read_bytes().startswith(b"%PDF")


def test_generate_lofter_pdf_creates_readable_pdf(tmp_path):
    target = tmp_path / "lofter.pdf"

    assert (
        generate_lofter_pdf(
            title="标题",
            author="作者",
            author_ip="author-ip",
            public_time="2024-03-07",
            url="https://author.lofter.com/post/1",
            content="正文内容",
            pdf_path=str(target),
        )
        is True
    )
    assert target.read_bytes().startswith(b"%PDF")


def test_generate_epub_creates_valid_archive(tmp_path):
    target = tmp_path / "book.epub"

    assert (
        generate_epub(
            title="电子书",
            author="作者",
            content_parts=["段落甲", "段落乙"],
            chapters_info=None,
            metadata_list=["Fandom: 测试"],
            filepath=str(target),
        )
        is True
    )
    assert target.exists()
    with zipfile.ZipFile(target) as archive:
        names = archive.namelist()
    assert any(name.endswith(".opf") for name in names)


def test_generate_epub_writes_one_entry_per_chapter(tmp_path):
    target = tmp_path / "multi.epub"

    assert (
        generate_epub(
            title="多章",
            author="作者",
            content_parts=[],
            chapters_info=[("第一章", ["甲"]), ("第二章", ["乙"])],
            metadata_list=None,
            filepath=str(target),
        )
        is True
    )
    with zipfile.ZipFile(target) as archive:
        names = archive.namelist()
    assert any("chapter_1" in name for name in names)
    assert any("chapter_2" in name for name in names)


def test_generate_epub_reports_failure_without_raising(tmp_path):
    """写入不可用路径时应返回 False 而不是抛异常。"""
    target = tmp_path / "missing-dir" / "book.epub"

    assert (
        generate_epub(
            title="失败",
            author="作者",
            content_parts=["甲"],
            chapters_info=None,
            metadata_list=None,
            filepath=str(target),
            log=lambda _message: None,
        )
        is False
    )
