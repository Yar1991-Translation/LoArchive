"""任务控制 API（/api/task/*）与 SSE 事件流。"""

import asyncio
import json

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from ..schemas import TaskStartPayload
from ..state import TaskManager
from . import get_task_manager

router = APIRouter()


@router.post("/api/task/start")
def start_task(payload: TaskStartPayload, manager: TaskManager = Depends(get_task_manager)):
    """启动任务。"""
    if manager.is_running():
        return {"success": False, "message": "已有任务在运行中"}

    try:
        params = payload.validated_params()
    except Exception as e:
        return {"success": False, "message": f"参数错误: {e}"}

    manager.start(payload.type, params)
    return {"success": True, "message": "任务已启动"}


@router.get("/api/task/status")
def get_task_status(manager: TaskManager = Depends(get_task_manager)):
    """获取任务状态（轮询回退用）。"""
    return manager.status()


@router.post("/api/task/stop")
def stop_task(manager: TaskManager = Depends(get_task_manager)):
    """停止任务（设置取消标志，爬虫在检查点中断）。"""
    manager.stop()
    return {"success": True, "message": "任务已停止"}


@router.get("/api/task/events")
async def task_events(request: Request, manager: TaskManager = Depends(get_task_manager)):
    """SSE 事件流：实时推送日志 / 进度 / 状态快照。"""
    q = manager.subscribe()

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.to_thread(q.get, True, 25.0)
                except Exception:
                    # 超时发送心跳，保持连接
                    yield {"event": "ping", "data": ""}
                    continue
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"], ensure_ascii=False),
                }
        finally:
            manager.unsubscribe(q)

    return EventSourceResponse(event_generator())
