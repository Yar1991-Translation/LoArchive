"""配置与应用设置 API（/api/config, /api/settings）。"""

import os

from fastapi import APIRouter, Depends

from ..config import ConfigStore
from ..schemas import ConfigPayload, SettingsPayload
from . import get_config_store

router = APIRouter()


@router.get("/api/config")
def get_config(store: ConfigStore = Depends(get_config_store)):
    """获取配置（授权码遮蔽返回，形状与原实现一致）。"""
    cfg = store.load()
    return {
        "login_key": cfg["login_key"],
        "login_auth": store.masked_auth(),
        "has_auth": bool(cfg["login_auth"]),
        "file_path": cfg["file_path"],
    }


@router.post("/api/config")
def save_config(payload: ConfigPayload, store: ConfigStore = Depends(get_config_store)):
    """保存登录信息到配置文件。"""
    store.set("login_key", payload.login_key)
    store.set("login_auth", payload.login_auth)
    store.save()
    return {"success": True, "message": "配置已保存"}


@router.get("/api/settings")
def get_settings(store: ConfigStore = Depends(get_config_store)):
    """获取应用设置。"""
    store.load()  # 确保加载最新配置
    return {
        "save_path": store.get("save_path", "./dir"),
        "dark_mode": store.get("dark_mode", False),
        "auto_dedup": store.get("auto_dedup", True),
        "notify_on_complete": store.get("notify_on_complete", True),
    }


@router.post("/api/settings")
def save_settings(payload: SettingsPayload, store: ConfigStore = Depends(get_config_store)):
    """保存应用设置。"""
    data = payload.model_dump(exclude_none=True)

    if "save_path" in data:
        save_path = data["save_path"]
        store.set("save_path", save_path)
        # 确保目录存在
        try:
            os.makedirs(save_path, exist_ok=True)
            os.makedirs(os.path.join(save_path, "img"), exist_ok=True)
            os.makedirs(os.path.join(save_path, "article"), exist_ok=True)
        except Exception as e:
            return {"success": False, "message": f"创建目录失败: {str(e)}"}
    if "dark_mode" in data:
        store.set("dark_mode", data["dark_mode"])
    if "auto_dedup" in data:
        store.set("auto_dedup", data["auto_dedup"])
    if "notify_on_complete" in data:
        store.set("notify_on_complete", data["notify_on_complete"])

    store.save()
    return {"success": True, "message": "设置已保存"}
