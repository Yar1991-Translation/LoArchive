"""共享测试夹具：临时数据目录与 FastAPI TestClient。"""

import pytest
from fastapi.testclient import TestClient

from loarchive.main import create_app


@pytest.fixture
def data_dir(tmp_path):
    """隔离的配置/历史/下载目录。"""
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    return tmp_path, downloads


@pytest.fixture
def client(tmp_path):
    """不托管前端静态文件的 TestClient（API 测试用）。"""
    app = create_app(data_dir=str(tmp_path / "data"), serve_frontend=False)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def config_store(tmp_path):
    """独立可用的 ConfigStore，指向临时文件。"""
    from loarchive.config import ConfigStore

    return ConfigStore(str(tmp_path / "config.json"))


@pytest.fixture
def history_manager(tmp_path):
    """独立可用的 HistoryManager，指向临时文件。"""
    from loarchive.history import HistoryManager

    return HistoryManager(str(tmp_path / "history.json"))
