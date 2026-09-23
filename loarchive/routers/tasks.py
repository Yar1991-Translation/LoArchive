"""任务控制 API（/api/task/*）与 SSE 事件流。"""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from ..schemas import MessageResponse, TaskStartPayload, TaskStatusResponse
from ..state import TaskManager
from . import get_task_manager

router = APIRouter()


@router.post("/api/task/start", response_model=MessageResponse)
def start_task(payload: TaskStartPayload, manager: TaskManager = Depends(get_task_manager)) -> dict:
    """启动任务；已有任务运行返回 409，参数错误返回 400。"""
    try:
        params = payload.validated_params()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误: {e}") from e

    if manager.is_running():
        raise HTTPException(status_code=409, detail="已有任务在运行中")

    try:
        manager.start(payload.type, params)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return {"message": "任务已启动"}


@router.get("/api/task/status", response_model=TaskStatusResponse)
def get_task_status(manager: TaskManager = Depends(get_task_manager)) -> dict:
    """获取任务状态（SSE 不可用时的轮询回退）。"""
    return manager.status()


@router.post("/api/task/stop", response_model=MessageResponse)
def stop_task(manager: TaskManager = Depends(get_task_manager)) -> dict:
    """停止任务（设置取消标志，爬虫在检查点中断）。"""
    manager.stop()
    return {"message": "已请求停止任务"}


@router.get("/api/task/events")
async def task_events(request: Request, manager: TaskManager = Depends(get_task_manager)):
    """SSE 事件流：实时推送日志 / 进度 / 状态快照。"""
    return EventSourceResponse(stream_task_events(request, manager))


async def stream_task_events(request: Request, manager: TaskManager):
    """产出 SSE 事件：实时推送日志 / 进度 / 状态快照。

    每秒醒来一次以便及时感知客户端断开；空闲约 15 秒发送一次心跳。
    """
    q = manager.subscribe()
    idle_ticks = 0
    try:
        while True:
            try:
                event = await asyncio.to_thread(q.get, True, 1.0)
            except Exception:
                idle_ticks += 1
                if await request.is_disconnected():
                    break
                if idle_ticks >= 15:
                    idle_ticks = 0
                    yield {"event": "ping", "data": ""}
                continue
            idle_ticks = 0
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"], ensure_ascii=False),
            }
    finally:
        manager.unsubscribe(q)
