"""爬虫公共基础：上下文与异常（re-export 便于爬虫模块引用）。"""

from ..state import SpiderContext, TaskCancelled

__all__ = ["SpiderContext", "TaskCancelled"]
