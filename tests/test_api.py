"""API 端点测试（FastAPI TestClient，爬虫层全部 mock）。"""

import time

import pytest


def test_root_serves_frontend_index(tmp_path):
    from fastapi.testclient import TestClient

    from loarchive.main import create_app

    app = create_app(data_dir=str(tmp_path / "data"))
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "LoArchive" in response.text
    assert 'type="module"' in response.text


def test_frontend_assets_are_served(tmp_path):
    from fastapi.testclient import TestClient

    from loarchive.main import create_app

    app = create_app(data_dir=str(tmp_path / "data"))
    with TestClient(app) as client:
        assert client.get("/js/main.js").status_code == 200
        assert client.get("/css/main.css").status_code == 200
        assert client.get("/js/api.js").status_code == 200


def test_frontend_assets_require_revalidation(tmp_path):
    """前端资源必须带 no-cache，否则浏览器会长时间复用旧样式/脚本。"""
    from fastapi.testclient import TestClient

    from loarchive.main import create_app

    app = create_app(data_dir=str(tmp_path / "data"))
    with TestClient(app) as client:
        page = client.get("/")
        css = client.get("/css/main.css")

    assert page.headers.get("cache-control") == "no-cache"
    assert css.headers.get("cache-control") == "no-cache"
    # 接口响应不受影响
    assert client.get("/api/task/status").headers.get("cache-control") is None


def test_select_dropdown_arrow_background_is_not_reset_by_specificity():
    """下拉箭头依赖 background-repeat/position/size 三个长属性。

    `select.form-input` 的特异度是 (0,1,1)，而带伪类（(0,2,0)）或带主题祖先类
    （(0,2,1)）的 `.form-input` 规则特异度更高，一旦这些规则使用 `background` 简写，
    就会把上述长属性重置为初始值，箭头便平铺满整个下拉框。
    基础规则 `.form-input { background: ... }` 特异度更低、随后被覆盖，属于合法写法。
    """
    import re
    from pathlib import Path

    css = (Path(__file__).resolve().parents[1] / "frontend" / "css" / "main.css").read_text(encoding="utf-8")
    rules = re.findall(r"([^{}]*\.form-input[^{}]*)\{([^{}]*)\}", css)

    assert any("select.form-input" in selector for selector, _ in rules), "未找到 select.form-input 基础规则"
    assert "background-repeat: no-repeat" in css

    higher_specificity = [
        selector.strip()
        for selector, declarations in rules
        if any(token in selector for token in (":hover", ":focus", ":active", "bw-mode", "dark-mode"))
        and re.search(r"(?m)^\s*background\s*:", declarations)
    ]
    assert not higher_specificity, f"这些规则用 background 简写重置了下拉箭头: {higher_specificity}"


# ---------- 配置 / 设置 ----------


def test_get_config_masks_auth(client):
    client.post("/api/config", json={"login_key": "Authorization", "login_auth": "0123456789abcdef"})

    data = client.get("/api/config").json()

    assert data["login_key"] == "Authorization"
    assert data["login_auth"] == "01234...bcdef"
    assert data["has_auth"] is True


def test_get_config_without_auth(client):
    data = client.get("/api/config").json()

    assert data["has_auth"] is False
    assert data["login_auth"] == ""


def test_settings_round_trip_and_creates_directories(client, tmp_path):
    target = tmp_path / "saved"

    response = client.post(
        "/api/settings",
        json={"save_path": str(target), "auto_dedup": False, "notify_on_complete": False},
    )

    assert response.json()["success"] is True
    assert (target / "img").is_dir()
    assert (target / "article").is_dir()

    settings = client.get("/api/settings").json()
    assert settings["save_path"] == str(target)
    assert settings["auto_dedup"] is False
    assert settings["notify_on_complete"] is False


def test_settings_partial_update_keeps_other_values(client):
    client.post("/api/settings", json={"auto_dedup": False})
    client.post("/api/settings", json={"notify_on_complete": False})

    settings = client.get("/api/settings").json()

    assert settings["auto_dedup"] is False
    assert settings["notify_on_complete"] is False


# ---------- 任务 ----------


def test_task_status_defaults_to_idle(client):
    status = client.get("/api/task/status").json()

    assert status["running"] is False
    assert status["progress"] == 0
    assert status["logs"] == []
    assert status["error"] is None


def test_start_task_rejects_invalid_params(client, monkeypatch):
    response = client.post(
        "/api/task/start",
        json={"type": "like_share_tag", "params": {"mode": "不存在的模式"}},
    )

    assert response.json()["success"] is False
    assert "参数错误" in response.json()["message"]


def test_start_task_runs_spider_and_publishes_logs(client, monkeypatch):
    import loarchive.spiders as spiders

    client.post("/api/config", json={"login_key": "LOFTER-PHONE-LOGIN-AUTH", "login_auth": "test-token"})

    def fake_run(ctx, params):
        ctx.log("mock 任务已运行")
        ctx.set_progress(42)

    monkeypatch.setitem(spiders.TASK_RUNNERS, "single_txt", fake_run)

    response = client.post(
        "/api/task/start",
        json={"type": "single_txt", "params": {"urls": ["https://example.com/post/1"]}},
    )

    assert response.json()["success"] is True

    for _ in range(50):
        status = client.get("/api/task/status").json()
        if not status["running"]:
            break
        time.sleep(0.1)

    assert status["running"] is False
    assert any("mock 任务已运行" in line for line in status["logs"])
    # 任务结束时进度置满、最后一条日志覆盖 message（沿用原实现行为）
    assert status["progress"] == 100
    assert status["message"] == "✅ 任务结束"


def test_start_task_requires_login_for_lofter(client):
    response = client.post(
        "/api/task/start",
        json={"type": "single_txt", "params": {"urls": ["https://example.com/post/1"]}},
    )

    assert response.json()["success"] is True

    for _ in range(50):
        status = client.get("/api/task/status").json()
        if not status["running"]:
            break
        time.sleep(0.1)

    assert "请先在设置中配置登录授权码" in status["error"]


def test_second_task_is_rejected_while_running(client, monkeypatch):
    import threading
    import time as time_module

    import loarchive.spiders as spiders

    release = threading.Event()

    def slow_run(ctx, params):
        release.wait(timeout=10)

    monkeypatch.setitem(spiders.TASK_RUNNERS, "ao3", slow_run)

    first = client.post("/api/task/start", json={"type": "ao3", "params": {"urls": ["https://ao3/works/1"]}})
    assert first.json()["success"] is True

    for _ in range(50):
        if client.get("/api/task/status").json()["running"]:
            break
        time_module.sleep(0.05)

    second = client.post("/api/task/start", json={"type": "ao3", "params": {"urls": ["https://ao3/works/2"]}})
    assert second.json()["success"] is False
    assert second.json()["message"] == "已有任务在运行中"

    release.set()


def test_stop_task_sets_cancel_flag(client, monkeypatch):
    import threading

    import loarchive.spiders as spiders

    started = threading.Event()

    def cancellable_run(ctx, params):
        started.set()
        for _ in range(100):
            ctx.check_cancel()
            threading.Event().wait(0.05)

    monkeypatch.setitem(spiders.TASK_RUNNERS, "ao3", cancellable_run)

    client.post("/api/task/start", json={"type": "ao3", "params": {"urls": ["https://ao3/works/1"]}})
    assert started.wait(timeout=5) is True

    assert client.post("/api/task/stop").json()["success"] is True

    for _ in range(50):
        status = client.get("/api/task/status").json()
        if not status["running"]:
            break
        time.sleep(0.1)

    assert status["running"] is False
    assert any("任务已停止" in line for line in status["logs"])
    # 被取消的任务不应被标记为错误
    assert status["error"] is None


# ---------- 文件 ----------


def test_list_files_reports_downloads(client, tmp_path):
    target = tmp_path / "downloads"
    (target / "img").mkdir(parents=True)
    (target / "img" / "a.jpg").write_bytes(b"fake")
    (target / "b.txt").write_text("text", encoding="utf-8")
    (target / "history.json").write_text("{}", encoding="utf-8")

    client.post("/api/settings", json={"save_path": str(target)})
    data = client.get("/api/files").json()

    names = {item["name"] for item in data["files"]}
    assert names == {"a.jpg", "b.txt"}
    assert data["total"] == 2

    by_name = {item["name"]: item for item in data["files"]}
    assert by_name["a.jpg"]["type"] == "image"
    assert by_name["b.txt"]["type"] == "text"


# ---------- 历史 ----------


def test_history_endpoints_round_trip(client):
    client.get("/api/history")

    assert client.post("/api/history/clear").json()["success"] is True

    data = client.get("/api/history").json()
    assert data["total"] == 0
    assert data["stats"] == {"total": 0, "images": 0, "articles": 0}


def test_history_check_respects_auto_dedup_switch(client, tmp_path):
    from loarchive.history import HistoryManager

    target = tmp_path / "downloads"
    client.post("/api/settings", json={"save_path": str(target)})
    app = client.app
    app.state.history.add("article", "https://example.com/1", "标题", "作者", "/tmp/1.txt")

    assert client.post("/api/history/check", json={"url": "https://example.com/1"}).json()["downloaded"] is True

    client.post("/api/settings", json={"auto_dedup": False})

    assert client.post("/api/history/check", json={"url": "https://example.com/1"}).json()["downloaded"] is False
    # 关闭开关不应删除已有记录
    assert HistoryManager(str(app.state.history.path)).is_downloaded("https://example.com/1") is True


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("", 2),
        ("?type=image", 1),
        ("?source=ao3", 1),
        ("?search=目标", 1),
    ],
)
def test_history_query_filters_via_api(client, query, expected):
    app = client.app
    app.state.history.add("image", "https://lofter.example/1", "目标图片", "作者", "/tmp/1.jpg", "lofter")
    app.state.history.add("ao3", "https://ao3.example/2", "AO3 文章", "作者", "/tmp/2.txt", "ao3")

    assert client.get(f"/api/history{query}").json()["total"] == expected
