"""Lofter 彩蛋（回礼）模块测试：纯函数解析与编排逻辑（全部离线）。"""

import pytest

from loarchive.errors import FetchError
from loarchive.spiders import lofter_egg
from loarchive.spiders.lofter_egg import (
    build_egg_headers,
    download_eggs_for_post,
    parse_post_ids,
    parse_return_gift,
    parse_unlocked_eggs,
)


class FakeCtx:
    """测试用 SpiderContext 替身：记录日志与配置。"""

    def __init__(self, config=None):
        self.config = config or {}
        self.logs = []

    def log(self, message):
        self.logs.append(message)


class FakeResponse:
    def __init__(self, payload=None, status_code=200, raw=None):
        self.status_code = status_code
        self._payload = payload
        self._raw = raw

    def json(self):
        if self._raw is not None:
            raise ValueError("not json")
        return self._payload


class FakeSession:
    """按调用顺序返回预设响应的会话替身。"""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.responses.pop(0)


@pytest.fixture
def patch_session(monkeypatch):
    def _patch(responses):
        fake = FakeSession(responses)
        monkeypatch.setattr(lofter_egg, "build_egg_session", lambda config: fake)
        return fake

    return _patch


# ---------- URL 解析 ----------


def test_parse_post_ids_decodes_hex_segments():
    post_id, blog_id = parse_post_ids("https://someone.lofter.com/post/af8ab31c_34e54e765")
    assert blog_id == int("af8ab31c", 16)
    assert post_id == int("34e54e765", 16)


def test_parse_post_ids_returns_none_for_non_post_links():
    assert parse_post_ids("https://someone.lofter.com/") == (None, None)
    assert parse_post_ids("https://www.lofter.com/tag/彩蛋") == (None, None)


# ---------- 鉴权头 ----------


def test_build_egg_headers_uses_phone_login_header():
    headers = build_egg_headers({"login_key": "LOFTER-PHONE-LOGIN-AUTH", "login_auth": "tok"})
    assert headers["lofter-phone-login-auth"] == "tok"


def test_build_egg_headers_uses_authorization_header():
    headers = build_egg_headers({"login_key": "Authorization", "login_auth": "tok"})
    assert headers["Authorization"] == "tok"


def test_build_egg_headers_web_login_has_no_mobile_header():
    headers = build_egg_headers({"login_key": "LOFTER_SESS", "login_auth": "tok"})
    assert "lofter-phone-login-auth" not in headers
    assert "Authorization" not in headers


# ---------- 已解锁筛选 ----------


def test_parse_unlocked_eggs_matches_gain_list():
    data = {
        "returnGifts": [
            {"id": 1, "title": "已解锁"},
            {"id": 2, "title": "未解锁"},
        ],
        "gainReturnGifts": [{"id": 1}],
    }
    unlocked = parse_unlocked_eggs(data)
    assert [g["id"] for g in unlocked] == [1]


def test_parse_unlocked_eggs_includes_gifts_with_inline_content():
    data = {"returnGifts": [{"id": 7, "content": "正文"}], "gainReturnGifts": []}
    assert [g["id"] for g in parse_unlocked_eggs(data)] == [7]


def test_parse_unlocked_eggs_empty_when_no_gifts():
    assert parse_unlocked_eggs({}) == []


# ---------- plan 解析 ----------


def test_parse_return_gift_extracts_content_and_image_urls():
    plan = {
        "title": "番外",
        "content": "正文内容",
        "planType": {"name": "彩蛋"},
        "images": [{"raw": "https://img/a.jpg", "baseImage": "https://img/a_small.jpg"}, {"baseImage": "x"}],
    }
    egg = parse_return_gift(plan)
    assert egg == {
        "title": "番外",
        "content": "正文内容",
        "plan_type": "彩蛋",
        "images": ["https://img/a.jpg", "x"],
    }


# ---------- 编排 ----------


def _support_info(return_gifts, gain=None):
    return {"code": 200, "ok": True, "data": {"returnGifts": return_gifts, "gainReturnGifts": gain or []}}


def test_orchestration_skips_locked_eggs_without_files(patch_session, tmp_path):
    patch_session([FakeResponse(_support_info([{"id": 9, "title": "锁住的彩蛋", "digest": "预览"}]))])
    ctx = FakeCtx({"login_key": "LOFTER-PHONE-LOGIN-AUTH", "login_auth": "t"})

    download_eggs_for_post(ctx, "https://a.lofter.com/post/1_2", str(tmp_path / "t"), str(tmp_path / "i"))

    assert any("未解锁" in line for line in ctx.logs)
    assert not (tmp_path / "t").exists()


def test_orchestration_saves_unlocked_egg_content_and_image(patch_session, monkeypatch, tmp_path):
    session = patch_session(
        [
            FakeResponse(_support_info([{"id": 5, "title": "番外"}], gain=[{"id": 5}])),
            FakeResponse(
                {
                    "code": 200,
                    "ok": True,
                    "data": {
                        "plan": {
                            "title": "番外",
                            "content": "彩蛋正文",
                            "planType": {"name": "彩蛋"},
                            "images": [{"raw": "https://img/e.jpg"}],
                        }
                    },
                }
            ),
        ]
    )
    monkeypatch.setattr(lofter_egg, "download_file", lambda url, path, referer="": open(path, "wb").write(b"img"))
    ctx = FakeCtx({"login_key": "LOFTER-PHONE-LOGIN-AUTH", "login_auth": "t"})
    text_dir = tmp_path / "t"
    image_dir = tmp_path / "i"

    download_eggs_for_post(ctx, "https://a.lofter.com/post/1_5", str(text_dir), str(image_dir))

    # myReturnGift 被正确调用
    assert any("myReturnGift" in url and params["id"] == 5 for url, params in session.calls)
    txt_files = list(text_dir.glob("*.txt"))
    assert len(txt_files) == 1
    assert "彩蛋正文" in txt_files[0].read_text(encoding="utf-8")
    assert any("已保存彩蛋" in line for line in ctx.logs)
    assert list(image_dir.glob("*.jpg"))


def test_orchestration_uses_inline_content_without_extra_request(patch_session, tmp_path):
    session = patch_session(
        [
            FakeResponse(
                _support_info(
                    [{"id": 3, "title": "自带正文", "content": "已并入帖子的内容"}],
                    gain=[{"id": 3}],
                )
            )
        ]
    )
    ctx = FakeCtx({})

    download_eggs_for_post(ctx, "https://a.lofter.com/post/1_3", str(tmp_path / "t"), str(tmp_path / "i"))

    # 内容已自带，不应再请求 myReturnGift
    assert len(session.calls) == 1
    assert any("已保存彩蛋" in line for line in ctx.logs)


def test_orchestration_reports_api_failure_without_raising(patch_session, tmp_path):
    patch_session([FakeResponse({"code": 500, "ok": False, "msg": "请先登录"}, status_code=200)])
    ctx = FakeCtx({})

    download_eggs_for_post(ctx, "https://a.lofter.com/post/1_2", str(tmp_path / "t"), str(tmp_path / "i"))

    assert any("彩蛋信息获取失败" in line for line in ctx.logs)
    assert not (tmp_path / "t").exists()


def test_orchestration_ignores_posts_without_eggs(patch_session, tmp_path):
    patch_session([FakeResponse(_support_info([]))])
    ctx = FakeCtx({})

    download_eggs_for_post(ctx, "https://a.lofter.com/post/1_2", str(tmp_path / "t"), str(tmp_path / "i"))

    assert ctx.logs == []


def test_orchestration_returns_silently_for_non_post_urls(tmp_path):
    ctx = FakeCtx({})
    download_eggs_for_post(ctx, "https://a.lofter.com/", str(tmp_path / "t"), str(tmp_path / "i"))
    assert ctx.logs == []


def test_fetch_error_raised_on_bad_envelope():
    """_get_json 对失败包络抛 FetchError（由编排层捕获转日志）。"""
    session = FakeSession([FakeResponse({"code": 401, "ok": False, "msg": "登录失效"})])
    with pytest.raises(FetchError):
        lofter_egg._get_json(session, "/v1.1/trade/gift/post/newSupportInfo", {"postId": 1, "blogId": 2})
