"""元信息 API（/api/version）。"""

from fastapi import APIRouter

from .. import __version__
from ..schemas import VersionResponse

router = APIRouter()


@router.get("/api/version", response_model=VersionResponse)
def get_version() -> dict:
    """返回应用版本（前端展示与更新检查的单一来源）。"""
    return {"version": __version__}
