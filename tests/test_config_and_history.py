"""配置与下载历史的读写、去重、分页与统计测试。"""

import json

from loarchive.config import DEFAULT_CONFIG, ConfigStore
from loarchive.history import compute_stats


def test_config_store_uses_defaults_when_file_missing(tmp_path):
    store = ConfigStore(str(tmp_path / "missing.json"))

    assert store.get("login_key") == DEFAULT_CONFIG["login_key"]
    assert store.get("auto_dedup") is True


def test_config_store_round_trips_values(tmp_path):
    path = tmp_path / "config.json"
    store = ConfigStore(str(path))
    store.set("login_auth", "secret-token-value-long")
    store.save()

    reloaded = ConfigStore(str(path))
    assert reloaded.get("login_auth") == "secret-token-value-long"


def test_config_store_loads_existing_file_without_clobbering_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"save_path": "D:/downloads"}), encoding="utf-8")

    store = ConfigStore(str(path))

    assert store.get("save_path") == "D:/downloads"
    assert store.get("login_key") == DEFAULT_CONFIG["login_key"]


def test_config_store_survives_corrupted_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{ not json", encoding="utf-8")

    store = ConfigStore(str(path))

    assert store.get("save_path") == DEFAULT_CONFIG["save_path"]


def test_masked_auth_hides_middle_of_long_token(tmp_path):
    store = ConfigStore(str(tmp_path / "config.json"))
    store.set("login_auth", "abcdefghijklmnop")

    # 与旧实现一致：取前 5 位 + 末 5 位
    assert store.masked_auth() == "abcde...lmnop"


def test_masked_auth_returns_short_token_unchanged(tmp_path):
    store = ConfigStore(str(tmp_path / "config.json"))
    store.set("login_auth", "short")

    assert store.masked_auth() == "short"


def test_history_add_and_is_downloaded(history_manager):
    assert history_manager.add("article", "https://example.com/1", "标题", "作者", "/tmp/f.txt") is True

    assert history_manager.is_downloaded("https://example.com/1") is True
    assert history_manager.is_downloaded("https://example.com/2") is False


def test_history_add_deduplicates_by_url(history_manager):
    history_manager.add("article", "https://example.com/1", "标题", "作者", "/tmp/f.txt")

    assert history_manager.add("article", "https://example.com/1", "另一个标题", "作者", "/tmp/g.txt") is False
    assert history_manager.query()["total"] == 1


def test_history_newest_records_come_first(history_manager):
    history_manager.add("article", "https://example.com/1", "第一篇", "作者", "/tmp/1.txt")
    history_manager.add("article", "https://example.com/2", "第二篇", "作者", "/tmp/2.txt")

    items = history_manager.query()["items"]

    assert [item["title"] for item in items] == ["第二篇", "第一篇"]


def test_history_fills_placeholder_title_and_author(history_manager):
    history_manager.add("image", "https://example.com/1", None, None, "/tmp/f.jpg")

    item = history_manager.query()["items"][0]

    assert item["title"] == "无标题"
    assert item["author"] == "未知作者"


def test_history_delete_removes_only_target(history_manager):
    history_manager.add("article", "https://example.com/1", "第一篇", "作者", "/tmp/1.txt")
    history_manager.add("article", "https://example.com/2", "第二篇", "作者", "/tmp/2.txt")
    target_id = history_manager.query()["items"][0]["id"]

    history_manager.delete(target_id)

    items = history_manager.query()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "第一篇"


def test_history_clear_empties_everything(history_manager):
    history_manager.add("article", "https://example.com/1", "标题", "作者", "/tmp/1.txt")

    assert history_manager.clear() is True
    assert history_manager.query()["total"] == 0
    assert history_manager.is_downloaded("https://example.com/1") is False


def test_history_query_filters_by_type_and_source(history_manager):
    history_manager.add("image", "https://lofter.example/1", "图片", "作者", "/tmp/1.jpg", "lofter")
    history_manager.add("ao3", "https://ao3.example/2", "文章", "作者", "/tmp/2.txt", "ao3")

    assert history_manager.query(filter_type="image")["total"] == 1
    assert history_manager.query(filter_source="ao3")["total"] == 1


def test_history_query_searches_title_author_and_url(history_manager):
    history_manager.add("article", "https://example.com/target", "目标标题", "某作者", "/tmp/1.txt")
    history_manager.add("article", "https://example.com/other", "其他", "别人", "/tmp/2.txt")

    assert history_manager.query(search="目标")["total"] == 1
    assert history_manager.query(search="某作者")["total"] == 1
    assert history_manager.query(search="target")["total"] == 1
    assert history_manager.query(search="不存在")["total"] == 0


def test_history_query_paginates_and_clamps_page(history_manager):
    for index in range(25):
        history_manager.add("article", f"https://example.com/{index}", f"第{index}篇", "作者", f"/tmp/{index}.txt")

    first_page = history_manager.query(page=1, per_page=10)
    last_page = history_manager.query(page=99, per_page=10)

    assert len(first_page["items"]) == 10
    assert first_page["total_pages"] == 3
    assert last_page["page"] == 3
    assert len(last_page["items"]) == 5


def test_history_query_clamps_per_page_into_supported_range(history_manager):
    history_manager.add("article", "https://example.com/1", "标题", "作者", "/tmp/1.txt")

    assert history_manager.query(per_page=999)["per_page"] == 100
    assert history_manager.query(per_page=1)["per_page"] == 10


def test_compute_stats_counts_images_and_articles():
    items = [
        {"type": "image"},
        {"type": "article"},
        {"type": "ao3"},
        {"type": "unknown"},
    ]

    assert compute_stats(items) == {"total": 4, "images": 1, "articles": 2}
