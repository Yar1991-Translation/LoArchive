"""API 路由模块与应用状态依赖注入。"""

from fastapi import Request

from ..config import ConfigStore
from ..history import HistoryManager
from ..state import TaskManager


def get_config_store(request: Request) -> ConfigStore:
    return request.app.state.config_store


def get_history(request: Request) -> HistoryManager:
    return request.app.state.history


def get_task_manager(request: Request) -> TaskManager:
    return request.app.state.task_manager
