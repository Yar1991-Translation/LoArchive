"""配置与应用设置 API（/api/config, /api/settings）。"""

import os

from fastapi import APIRouter, Depends, HTTPException

from ..config import ConfigStore
from ..schemas import ConfigPayload, ConfigResponse, MessageResponse, SettingsPayload, SettingsResponse
from . import get_config_store

router = APIRouter()


@router.get("/api/config", response_model=ConfigResponse)
def get_config(store: ConfigStore = Depends(get_config_store)) -> dict:
    """获取配置（授权码遮蔽返回）。"""
    cfg = store.load()
    return {
        "login_key": cfg["login_key"],
        "login_auth": store.masked_auth(),
        "has_auth": bool(cfg["login_auth"]),
        "file_path": cfg["file_path"],
    }


@router.post("/api/config", response_model=MessageResponse)
def save_config(payload: ConfigPayload, store: ConfigStore = Depends(get_config_store)) -> dict:
    """保存登录信息到配置文件。"""
    store.set("login_key", payload.login_key)
    store.set("login_auth", payload.login_auth)
    store.save()
    return {"message": "配置已保存"}


@router.get("/api/settings", response_model=SettingsResponse)
def get_settings(store: ConfigStore = Depends(get_config_store)) -> dict:
    """获取应用设置。"""
    store.load()  # 确保加载最新配置
    return {
        "save_path": store.get("save_path", "./dir"),
        "auto_dedup": store.get("auto_dedup", True),
        "notify_on_complete": store.get("notify_on_complete", True),
    }


@router.post("/api/settings", response_model=MessageResponse)
def save_settings(payload: SettingsPayload, store: ConfigStore = Depends(get_config_store)) -> dict:
    """保存应用设置（部分更新）。"""
    data = payload.model_dump(exclude_none=True)

    if "save_path" in data:
        save_path = data["save_path"]
        try:
            os.makedirs(save_path, exist_ok=True)
            os.makedirs(os.path.join(save_path, "img"), exist_ok=True)
            os.makedirs(os.path.join(save_path, "article"), exist_ok=True)
        except OSError as e:
            raise HTTPException(status_code=400, detail=f"创建目录失败: {e}") from e
        store.set("save_path", save_path)
    if "auto_dedup" in data:
        store.set("auto_dedup", data["auto_dedup"])
    if "notify_on_complete" in data:
        store.set("notify_on_complete", data["notify_on_complete"])

    store.save()
    return {"message": "设置已保存"}
