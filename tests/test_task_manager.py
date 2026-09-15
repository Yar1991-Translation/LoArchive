"""TaskManager 与 SSE 事件流测试。"""

import json
import queue
import time

import pytest

from loarchive.config import ConfigStore
from loarchive.history import HistoryManager
from loarchive.state import SpiderContext, TaskCancelled, TaskManager


@pytest.fixture
def manager(tmp_path):
    return TaskManager(ConfigStore(str(tmp_path / "config.json")), HistoryManager(str(tmp_path / "history.json")))


def drain(queue_, timeout=5.0):
    """取出队列中已到达的全部事件。"""
    events = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            events.append(queue_.get(timeout=0.2))
        except Exception:
            break
    return events


def test_subscribe_delivers_snapshot_immediately(manager):
    queue_ = manager.subscribe()

    event = queue_.get(timeout=1)

    assert event["event"] == "snapshot"
    assert event["data"]["running"] is False
    assert event["data"]["progress"] == 0


def test_log_and_progress_are_published_to_subscribers(manager):
    queue_ = manager.subscribe()
    queue_.get(timeout=1)  # snapshot

    manager.log("hello")
    manager.set_progress(30)

    events = drain(queue_)
    kinds = [e["event"] for e in events]

    assert "log" in kinds
    assert "progress" in kinds
    log_event = next(e for e in events if e["event"] == "log")
    assert log_event["data"]["message"] == "hello"


def test_progress_is_clamped(manager):
    manager.set_progress(500)
    assert manager.status()["progress"] == 100

    manager.set_progress(-20)
    assert manager.status()["progress"] == 0


def test_log_history_is_capped(manager):
    for index in range(250):
        manager.log(f"line {index}")

    logs = manager.status()["logs"]

    assert len(logs) == 200
    assert "line 249" in logs[-1]
    assert "line 0" not in "".join(logs)


def test_unsubscribe_stops_delivery(manager):
    queue_ = manager.subscribe()
    manager.unsubscribe(queue_)
    queue_.get(timeout=1)  # 排掉已有的 snapshot

    manager.log("after unsubscribe")

    with pytest.raises(queue.Empty):
        queue_.get(timeout=0.3)


def test_spider_context_reports_cancellation(manager):
    ctx = SpiderContext(manager)
    assert ctx.cancelled is False

    manager.stop()

    assert ctx.cancelled is True
    with pytest.raises(TaskCancelled):
        ctx.check_cancel()


def test_spider_context_respects_auto_dedup_switch(manager, tmp_path):
    manager.history.add("article", "https://example.com/1", "标题", "作者", "/tmp/1.txt")
    ctx = SpiderContext(manager)

    assert ctx.is_downloaded("https://example.com/1") is True

    manager.config_store.set("auto_dedup", False)
    assert ctx.is_downloaded("https://example.com/1") is False


def test_task_failure_is_recorded_as_error(manager, monkeypatch):
    import loarchive.spiders as spiders

    def boom(ctx, params):
        raise RuntimeError("炸了")

    monkeypatch.setitem(spiders.TASK_RUNNERS, "ao3", boom)
    manager.start("ao3", {})

    for _ in range(50):
        if not manager.is_running():
            break
        time.sleep(0.05)

    status = manager.status()
    assert status["error"] == "炸了"
    assert any("任务出错" in line for line in status["logs"])


class FakeRequest:
    """模拟客户端：前 N 次检查时视为在线，之后视为断开。"""

    def __init__(self, disconnect_after=1):
        self.calls = 0
        self.disconnect_after = disconnect_after

    async def is_disconnected(self) -> bool:
        self.calls += 1
        return self.calls > self.disconnect_after


def test_stream_task_events_emits_snapshot_then_stops_on_disconnect(manager):
    import asyncio

    from loarchive.routers.tasks import stream_task_events

    async def collect():
        events = []
        generator = stream_task_events(FakeRequest(), manager)
        async for event in generator:
            events.append(event)
            if len(events) >= 1:
                break
        await generator.aclose()
        return events

    events = asyncio.run(collect())

    assert events[0]["event"] == "snapshot"
    assert json.loads(events[0]["data"])["running"] is False


def test_stream_task_events_unsubscribes_on_exit(manager):
    import asyncio

    from loarchive.routers.tasks import stream_task_events

    async def consume_one_then_close():
        generator = stream_task_events(FakeRequest(), manager)
        await generator.__anext__()
        await generator.aclose()

    asyncio.run(consume_one_then_close())

    assert manager._subscribers == []
