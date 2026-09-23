"""已下载文件列表 API（/api/files）。"""

import os

from fastapi import APIRouter, Depends

from ..config import ConfigStore
from ..schemas import FilesResponse
from . import get_config_store

router = APIRouter()

IMAGE_EXTENSIONS = (".jpg", ".png", ".gif", ".jpeg")


@router.get("/api/files", response_model=FilesResponse)
def list_files(store: ConfigStore = Depends(get_config_store)) -> dict:
    """列出已下载的文件（最多 200 条）。"""
    base_path = store.get("save_path", store.get("file_path", "./dir"))
    files = []

    if os.path.exists(base_path):
        for root, _dirs, filenames in os.walk(base_path):
            for filename in filenames:
                if not filename.endswith(".json") and not filename.startswith("."):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, base_path)
                    file_size = os.path.getsize(full_path)
                    files.append(
                        {
                            "name": filename,
                            "path": rel_path,
                            "size": file_size,
                            "type": "image" if filename.lower().endswith(IMAGE_EXTENSIONS) else "text",
                        }
                    )

    # 按名称排序，最新的在前
    files.sort(key=lambda x: x["name"], reverse=True)
    return {"files": files[:200], "total": len(files)}
