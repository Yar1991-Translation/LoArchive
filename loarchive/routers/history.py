"""下载历史 API（/api/history*）。"""

from fastapi import APIRouter, Depends, Query

from ..config import ConfigStore
from ..history import HistoryManager
from ..schemas import HistoryCheckPayload
from . import get_config_store, get_history

router = APIRouter()


@router.get("/api/history")
def list_history(
    page: int = Query(1),
    per_page: int = Query(20),
    type: str = Query(""),
    source: str = Query(""),
    search: str = Query(""),
    history: HistoryManager = Depends(get_history),
):
    """分页获取下载历史（形状与原实现一致）。"""
    return history.query(
        page=page,
        per_page=per_page,
        filter_type=type,
        filter_source=source,
        search=search.strip(),
    )


@router.post("/api/history/clear")
def clear_history(history: HistoryManager = Depends(get_history)):
    """清空下载历史。"""
    result = history.clear()
    if result:
        return {"success": True, "message": "历史记录已清空"}
    return {"success": False, "message": "清空失败"}


@router.delete("/api/history/delete/{item_id}")
def delete_history_item(item_id: str, history: HistoryManager = Depends(get_history)):
    """删除单条历史记录。"""
    history.delete(item_id)
    return {"success": True, "message": "记录已删除"}


@router.post("/api/history/check")
def check_downloaded(
    payload: HistoryCheckPayload,
    history: HistoryManager = Depends(get_history),
    store: ConfigStore = Depends(get_config_store),
):
    """检查URL是否已下载（自动去重关闭时恒为 False，与原实现一致）。"""
    if not store.get("auto_dedup", True):
        downloaded = False
    else:
        downloaded = history.is_downloaded(payload.url)
    return {"downloaded": downloaded, "url": payload.url}
