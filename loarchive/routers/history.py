"""下载历史 API（/api/history*）。"""

from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import ConfigStore
from ..history import HistoryManager
from ..schemas import (
    HistoryCheckPayload,
    HistoryCheckResponse,
    HistoryQueryResponse,
    MessageResponse,
)
from . import get_config_store, get_history

router = APIRouter()


@router.get("/api/history", response_model=HistoryQueryResponse)
def list_history(
    page: int = Query(1),
    per_page: int = Query(20),
    type: str = Query(""),
    source: str = Query(""),
    search: str = Query(""),
    history: HistoryManager = Depends(get_history),
) -> dict:
    """分页获取下载历史。"""
    return history.query(
        page=page,
        per_page=per_page,
        filter_type=type,
        filter_source=source,
        search=search.strip(),
    )


@router.post("/api/history/clear", response_model=MessageResponse)
def clear_history(history: HistoryManager = Depends(get_history)) -> dict:
    """清空下载历史。"""
    history.clear()
    return {"message": "历史记录已清空"}


@router.delete("/api/history/delete/{item_id}", response_model=MessageResponse)
def delete_history_item(item_id: str, history: HistoryManager = Depends(get_history)) -> dict:
    """删除单条历史记录；记录不存在返回 404。"""
    if not history.delete(item_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"message": "记录已删除"}


@router.post("/api/history/check", response_model=HistoryCheckResponse)
def check_downloaded(
    payload: HistoryCheckPayload,
    history: HistoryManager = Depends(get_history),
    store: ConfigStore = Depends(get_config_store),
) -> dict:
    """检查 URL 是否已下载（自动去重关闭时恒为 False）。"""
    if not store.get("auto_dedup", True):
        downloaded = False
    else:
        downloaded = history.is_downloaded(payload.url)
    return {"downloaded": downloaded, "url": payload.url}
