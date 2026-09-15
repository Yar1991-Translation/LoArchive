"""FastAPI 应用工厂与 uvicorn 启动入口。"""

import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import ConfigStore
from .history import HistoryManager
from .paths import CONFIG_FILENAME, HISTORY_FILENAME, get_data_dir, get_resource_path, migrate_legacy_data
from .routers import config as config_router
from .routers import files as files_router
from .routers import history as history_router
from .routers import tasks as tasks_router
from .state import TaskManager


def create_app(data_dir: str | None = None, serve_frontend: bool = True) -> FastAPI:
    """创建 FastAPI 应用。

    data_dir: 配置/历史文件目录（默认按环境自动解析；测试可注入临时目录）。
    serve_frontend: 是否托管 frontend/ 静态文件（浏览器开发模式）。
    """
    data_dir = data_dir or get_data_dir()
    os.makedirs(data_dir, exist_ok=True)

    # 打包环境首次启动时，导入安装目录旁的旧版配置/历史（不覆盖已有数据）
    migrated = migrate_legacy_data(data_dir)
    if migrated:
        print(f"已迁移旧版数据到 {data_dir}: {', '.join(migrated)}")

    config_store = ConfigStore(os.path.join(data_dir, CONFIG_FILENAME))
    history = HistoryManager(os.path.join(data_dir, HISTORY_FILENAME))
    task_manager = TaskManager(config_store, history)

    app = FastAPI(title="LoArchive", version=__version__)
    app.state.config_store = config_store
    app.state.history = history
    app.state.task_manager = task_manager

    # Tauri webview 从应用内协议加载页面，跨域调用 localhost:5000
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def revalidate_frontend_assets(request, call_next):
        """前端资源要求每次使用前回源校验。

        前端是无构建、无版本号的文件（index.html / main.css / js 模块），静态挂载
        默认只给 ETag 与 Last-Modified，浏览器会按启发式规则长时间复用缓存，
        导致升级应用后 UI 修复不生效。no-cache 表示「用前必须校验」，
        内容未变时仍返回 304，本地服务下开销可忽略。
        """
        response = await call_next(request)
        if not request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

    app.include_router(config_router.router)
    app.include_router(tasks_router.router)
    app.include_router(files_router.router)
    app.include_router(history_router.router)

    # 确保保存目录存在（与原启动行为一致）
    save_path = config_store.get("save_path", "./dir")
    for d in (save_path, os.path.join(save_path, "img"), os.path.join(save_path, "article")):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            print(f"创建保存目录失败 {d}: {e}")

    if serve_frontend:
        frontend_dir = get_resource_path("frontend")
        if os.path.isdir(frontend_dir):
            # 挂在最后：/api/* 路由优先，其余路径回退到静态文件（含 / -> index.html）
            app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


def ensure_standard_streams() -> None:
    """保证 stdout / stderr 可用。

    PyInstaller 的窗口模式（--noconsole）下这两个流是 None，而 uvicorn 在配置
    日志时会调用 sys.stdout.isatty()，导致应用启动即崩溃。这里退化为 os.devnull。
    """
    for name in ("stdout", "stderr"):
        if getattr(sys, name, None) is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))


def run(host: str = "0.0.0.0", port: int = 5000) -> None:
    """以 uvicorn 启动应用（供 run.py / PyInstaller 入口调用）。"""
    import uvicorn

    ensure_standard_streams()

    app = create_app()

    save_path = app.state.config_store.get("save_path", "./dir")
    print("=" * 50)
    print("LoArchive Web Application")
    print("=" * 50)
    print(f"保存路径: {save_path}")
    print("Visit http://localhost:5000 to start")
    print("=" * 50)

    uvicorn.run(app, host=host, port=port, log_level="info")
