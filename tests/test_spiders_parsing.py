"""爬虫纯解析逻辑测试（不发起任何网络请求）。"""

from lxml.html import etree

from loarchive.spiders.ao3 import (
    extract_chapter,
    extract_page_content,
    extract_work_metadata,
    extract_work_title_author,
    safe_filename,
)
from loarchive.spiders.lofter_author import parse_archive_records
from loarchive.spiders.lofter_collection import parse_fav_info
from loarchive.spiders.lofter_single import extract_article_text, extract_public_time, extract_title, find_lofter_images

# ---------- Lofter 单篇 ----------


def test_extract_public_time_normalizes_separators():
    assert extract_public_time("<span>2024/03/07</span>") == "2024-03-07"
    assert extract_public_time("<span>2024.03.07</span>") == "2024-03-07"
    assert extract_public_time("<span>2024-03-07</span>") == "2024-03-07"


def test_find_lofter_images_filters_thumbnails():
    html = """
    <img src="https://imglf0.lf127.net/photo.jpg?imageView2/2/w/1080">
    <img src="https://imglf1.lf127.net/small.jpg?imageView&thumbnail=64x64">
    """

    assert find_lofter_images(html) == ["https://imglf0.lf127.net/photo.jpg?"]


def test_extract_title_reads_first_h2():
    tree = etree.HTML("<h2> 标题文本 </h2><h2>第二标题</h2>")

    assert extract_title(tree) == "标题文本"


def test_extract_title_returns_empty_when_missing():
    assert extract_title(etree.HTML("<div>没有标题</div>")) == ""


def test_extract_article_text_prefers_content_div():
    tree = etree.HTML('<div class="content"><p>第一段</p><p>第二段</p></div>')

    assert extract_article_text(tree, "") == "第一段\n第二段"


def test_extract_article_text_falls_back_to_paragraphs():
    tree = etree.HTML("<article><p>甲</p><p>乙</p></article>")

    assert extract_article_text(tree, "") == "甲\n\n乙"


def test_extract_article_text_skips_full_page_fallback_when_disabled():
    """作者文章批量提取时，纯图片博客不应产生整页噪音文本。"""
    tree = etree.HTML("<div>只有无关页面内容</div>")

    assert extract_article_text(tree, "", allow_full_fallback=False) == ""


def test_extract_article_text_returns_placeholder_when_parsing_fails(monkeypatch):
    tree = etree.HTML("<div></div>")
    monkeypatch.setattr("html2text.HTML2Text", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    assert extract_article_text(tree, "<html></html>") == "无法解析正文内容"


# ---------- Lofter 作者归档 ----------


def test_parse_archive_records_skips_unparsable_entries():
    records = [
        's0.permalink="post-abc";s0.time=1704067200000;',
        "完全无关的内容",
    ]

    parsed = parse_archive_records(records)

    assert len(parsed) == 1
    assert parsed[0]["permalink"] == "post-abc"
    assert parsed[0]["has_img"] is False


def test_parse_archive_records_marks_image_posts():
    records = ['s0.permalink="post-img";s0.time=1704067200000;s0.imgurl="https://x/y.jpg";']

    parsed = parse_archive_records(records)

    assert parsed[0]["has_img"] is True
    assert parsed[0]["permalink"] == "post-img"


# ---------- Lofter 喜欢/推荐/Tag ----------


def test_parse_fav_info_extracts_core_fields():
    fav_info = (
        's0.blogPageUrl="https://author.lofter.com/post/1";'
        's0.blogNickName="\\\\u4f5c\\\\u8005";'
        "s0.publishTime=1704067200000;"
        's0.title="\\\\u6807\\\\u9898";'
    )

    blog = parse_fav_info(fav_info)

    assert blog["url"] == "https://author.lofter.com/post/1"
    assert blog["author_ip"] == "author"


def test_parse_fav_info_returns_none_without_blog_url():
    assert parse_fav_info('s0.title="no url";') is None


def test_parse_fav_info_extracts_image_urls():
    fav_info = (
        's0.blogPageUrl="https://author.lofter.com/post/1";'
        "originPhotoLinks=\"[{'raw': 'https://img/raw.jpg'}, {'orign': 'https://img/x.jpg?imageView'}]\";"
    )

    blog = parse_fav_info(fav_info)

    assert blog["img_urls"] == ["https://img/raw.jpg", "https://img/x.jpg"]
    assert blog["has_img"] is True


# ---------- AO3 ----------


def test_safe_filename_replaces_reserved_characters_and_truncates():
    # 保留旧实现行为：非法字符先替换为下划线，随后与空白一并折叠为单个空格
    assert safe_filename('a<b>c:d"e/f\\g|h?i*j') == "a b c d e f g h i j"
    assert len(safe_filename("x" * 200)) == 100
    assert safe_filename("") == "untitled"


def test_extract_work_title_author():
    html = """
    <h2 class="title heading">作品标题</h2>
    <a rel="author">作者名</a>
    """

    assert extract_work_title_author(html) == ("作品标题", "作者名")


def test_extract_work_title_author_uses_placeholders_when_missing():
    assert extract_work_title_author("<div>空</div>") == ("未知标题", "未知作者")


def test_extract_work_metadata_collects_fields():
    tree = etree.HTML(
        """
        <dl class="work meta group">
          <dd class="fandom tags"><a>Fandom A</a><a>Fandom B</a></dd>
          <dd class="rating tags"><a>Teen And Up Audiences</a></dd>
          <dd class="warning tags"><a>No Archive Warnings Apply</a></dd>
          <dd class="relationship tags"><a>A/B</a></dd>
          <dd class="character tags"><a>A</a></dd>
          <dd class="freeform tags"><a>Fluff</a></dd>
          <dd class="words">1200</dd>
          <dd class="chapters">1/1</dd>
        </dl>
        """
    )

    metadata = extract_work_metadata(tree)

    assert "Fandom: Fandom A, Fandom B" in metadata
    assert "Rating: Teen And Up Audiences" in metadata
    assert "Relationships: A/B" in metadata
    assert "\nWords: 1200" in metadata
    assert "Chapters: 1/1" in metadata


def test_extract_work_metadata_returns_empty_when_disabled():
    tree = etree.HTML('<dd class="fandom tags"><a>Fandom A</a></dd>')

    assert extract_work_metadata(tree, save_metadata=False) == []


def test_extract_page_content_reads_userstuff_paragraphs():
    tree = etree.HTML('<div class="userstuff module"><p>第一段</p><p>第二段</p></div>')

    assert extract_page_content(tree) == ["第一段", "第二段"]


def test_extract_chapter_uses_fallback_title():
    tree = etree.HTML('<div class="userstuff module"><p>正文</p></div>')

    title, content = extract_chapter(tree, 2)

    assert title == "第 3 章"
    assert content == ["正文"]
