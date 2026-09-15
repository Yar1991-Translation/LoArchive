"""工具函数测试：文件名清洗、图片 URL 过滤、图片类型推断。"""

from loarchive.utils import filter_lofter_image_urls, get_headers, guess_image_type, sanitize_filename


def test_sanitize_filename_replaces_path_separators():
    assert sanitize_filename("a/b\\c") == "a&b&c"


def test_sanitize_filename_replaces_windows_reserved_characters():
    assert sanitize_filename('a<b>c:d"e?f*g|h') == "a《b》c：d'e？f·g&h"


def test_sanitize_filename_strips_control_whitespace():
    assert sanitize_filename("  a\nb\tc\r  ") == "ab c"


def test_filter_lofter_image_urls_drops_html_escaped_and_thumbnail_urls():
    urls = [
        "https://imglf0.lf127.net/a.jpg?imageView&x=1&amp;y=2",
        "https://imglf0.lf127.net/b.jpg?imageView&thumbnail=64x64",
        "https://imglf0.lf127.net/c.jpg",
    ]

    assert filter_lofter_image_urls(urls) == ["https://imglf0.lf127.net/c.jpg"]


def test_filter_lofter_image_urls_deduplicates_and_strips_imageview():
    urls = [
        "https://imglf0.lf127.net/d.jpg?imageView2/2/w/1080",
        "https://imglf0.lf127.net/d.jpg?imageView2/2/w/1080",
    ]

    assert filter_lofter_image_urls(urls) == ["https://imglf0.lf127.net/d.jpg?"]


def test_guess_image_type():
    assert guess_image_type("https://x/a.gif") == "gif"
    assert guess_image_type("https://x/a.PNG".lower()) == "png"
    assert guess_image_type("https://x/a.webp.jpg") == "jpg"


def test_get_headers_returns_independent_copy():
    first = get_headers()
    first["Referer"] = "https://example.com"

    assert "Referer" not in get_headers()
