"""应用工厂与启动相关行为测试。"""

import os
import sys

from loarchive.main import ensure_standard_streams


def test_create_app_creates_data_dir(tmp_path):
    from loarchive.main import create_app

    data_dir = tmp_path / "nested" / "data"
    assert not data_dir.exists()

    create_app(data_dir=str(data_dir), serve_frontend=False)

    assert data_dir.is_dir()


def test_create_app_seeds_save_directories(tmp_path):
    from loarchive.main import create_app

    downloads = tmp_path / "downloads"
    data_dir = tmp_path / "data"
    app = create_app(data_dir=str(data_dir), serve_frontend=False)
    app.state.config_store.set("save_path", str(downloads))
    app.state.config_store.save()

    create_app(data_dir=str(data_dir), serve_frontend=False)

    assert (downloads / "img").is_dir()
    assert (downloads / "article").is_dir()


def test_ensure_standard_streams_restores_missing_streams(monkeypatch):
    """PyInstaller 窗口模式下 sys.stdout/stderr 为 None，uvicorn 会因此崩溃。"""
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)

    ensure_standard_streams()

    assert sys.stdout is not None
    assert sys.stderr is not None
    # uvicorn 的日志格式化器会调用 isatty()
    assert hasattr(sys.stdout, "isatty")
    sys.stdout.close()
    sys.stderr.close()


def test_ensure_standard_streams_leaves_working_streams_untouched():
    original = sys.stdout

    ensure_standard_streams()

    assert sys.stdout is original


def test_run_passes_through_uvicorn_without_raising(monkeypatch):
    """run() 应先修复标准流，再把应用交给 uvicorn（此处用桩替代真实启动）。"""
    from loarchive import main

    captured = {}

    def fake_run(app, host, port, log_level):
        captured["host"] = host
        captured["port"] = port
        captured["title"] = app.title

    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setitem(sys.modules, "uvicorn", type("U", (), {"run": staticmethod(fake_run)}))

    main.run(host="127.0.0.1", port=5099)

    assert captured == {"host": "127.0.0.1", "port": 5099, "title": "LoArchive"}
    assert os.devnull in (sys.stdout.name, sys.stderr.name)
    sys.stdout.close()
    sys.stderr.close()
