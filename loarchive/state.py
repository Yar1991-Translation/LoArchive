"""任务生命周期管理：TaskManager + SpiderContext + SSE 事件广播。"""

import queue
import threading
import time
import traceback

from .config import ConfigStore
from .errors import TaskCancelled
from .history import HistoryManager
from .logsetup import get_logger

logger = get_logger("task")

MAX_LOG_LINES = 200


class SpiderContext:
    """注入给爬虫的上下文：日志、进度、取消检查、配置与历史。"""

    def __init__(self, manager: "TaskManager"):
        self._manager = manager

    @property
    def config(self) -> dict:
        return self._manager.config_store.data

    @property
    def history(self) -> HistoryManager:
        return self._manager.history

    def log(self, message: str) -> None:
        self._manager.log(message)

    def set_progress(self, percent: int) -> None:
        self._manager.set_progress(percent)

    @property
    def cancelled(self) -> bool:
        return self._manager.cancelled

    def check_cancel(self) -> None:
        if self.cancelled:
            raise TaskCancelled()

    def add_history(self, item_type, url, title, author, file_path, source="lofter") -> bool:
        return self._manager.history.add(item_type, url, title, author, file_path, source)

    def is_downloaded(self, url: str) -> bool:
        """自动去重检查（尊重配置开关）。"""
        if not self.config.get("auto_dedup", True):
            return False
        return self._manager.history.is_downloaded(url)


class TaskManager:
    """管理爬虫工作线程、任务状态、取消标志与事件订阅。"""

    def __init__(self, config_store: ConfigStore, history: HistoryManager):
        self.config_store = config_store
        self.history = history
        self._lock = threading.Lock()
        self._cancel = threading.Event()
        self._thread: threading.Thread | None = None
        self._subscribers: list[queue.Queue] = []
        self._status = {
            "running": False,
            "current_task": None,
            "progress": 0,
            "message": "",
            "logs": [],
            "error": None,
        }

    # ---------- 状态 ----------

    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

    def is_running(self) -> bool:
        with self._lock:
            return self._status["running"]

    def status(self) -> dict:
        with self._lock:
            return {
                "running": self._status["running"],
                "current_task": self._status["current_task"],
                "progress": self._status["progress"],
                "message": self._status["message"],
                "logs": list(self._status["logs"]),
                "error": self._status["error"],
            }

    # ---------- 生命周期 ----------

    def start(self, task_type: str, params: dict) -> None:
        """启动任务；已有任务运行时抛出 RuntimeError。"""
        with self._lock:
            if self._status["running"]:
                raise RuntimeError("已有任务在运行中")
            self._status.update(
                {
                    "running": True,
                    "current_task": task_type,
                    "progress": 0,
                    "message": "",
                    "logs": [],
                    "error": None,
                }
            )
            self._cancel.clear()
            self._thread = threading.Thread(target=self._run, args=(task_type, params), daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """请求停止任务：设置取消标志，爬虫在下一检查点中断。"""
        self._cancel.set()
        self.log("⚠️ 收到停止请求，正在停止任务...")

    def _run(self, task_type: str, params: dict) -> None:
        from .spiders import TASK_RUNNERS

        ctx = SpiderContext(self)
        try:
            self.config_store.load()  # 重新加载配置（与原行为一致）

            runner = TASK_RUNNERS.get(task_type)
            if task_type == "ao3":
                runner(ctx, params)
            elif not self.config_store.get("login_auth"):
                raise Exception("请先在设置中配置登录授权码！")
            elif runner is not None:
                runner(ctx, params)
            else:
                self.log(f"❌ 未知的任务类型: {task_type}")
        except TaskCancelled:
            self.log("⏹️ 任务已停止")
        except Exception as e:
            with self._lock:
                self._status["error"] = str(e)
            logger.exception("任务 %s 执行失败", task_type)
            self.log(f"❌ 任务出错: {e}")
            self.log(traceback.format_exc())
        finally:
            with self._lock:
                self._status["running"] = False
                self._status["progress"] = 100
            self.log("✅ 任务结束")
            self._publish({"event": "done", "data": self.status()})

    # ---------- 日志 / 进度 ----------

    def log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        with self._lock:
            self._status["logs"].append(log_entry)
            self._status["message"] = message
            if len(self._status["logs"]) > MAX_LOG_LINES:
                self._status["logs"] = self._status["logs"][-MAX_LOG_LINES:]
        logger.info("%s", message)
        self._publish({"event": "log", "data": {"line": log_entry, "message": message}})

    def set_progress(self, percent: int) -> None:
        percent = max(0, min(100, int(percent)))
        with self._lock:
            self._status["progress"] = percent
        self._publish({"event": "progress", "data": {"progress": percent}})

    # ---------- 事件订阅（SSE） ----------

    def subscribe(self) -> queue.Queue:
        """订阅任务事件；订阅后立即收到一份状态快照。"""
        q: queue.Queue = queue.Queue(maxsize=500)
        with self._lock:
            self._subscribers.append(q)
        q.put({"event": "snapshot", "data": self.status()})
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def _publish(self, event: dict) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for q in subscribers:
            try:
                q.put_nowait(event)
            except queue.Full:
                pass
