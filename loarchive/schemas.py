"""API 请求体（按任务类型校验参数）与响应体的 Pydantic 模型。"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------- 任务参数模型（请求体） ----------


class LstParams(BaseModel):
    """喜欢/推荐/Tag 任务参数。"""

    url: str = ""
    mode: Literal["like1", "like2", "share", "tag"] = "like2"
    save_mode: dict[str, Any] = Field(default_factory=lambda: {"article": 1, "text": 1, "long article": 1, "img": 1})
    start_time: str = ""
    export_pdf: bool = False


class AuthorImgParams(BaseModel):
    author_url: str = ""
    start_time: str = ""
    end_time: str = ""


class AuthorTxtParams(BaseModel):
    author_url: str = ""


class SingleParams(BaseModel):
    urls: list[str] = Field(default_factory=list)


class Ao3Params(BaseModel):
    urls: list[str] = Field(default_factory=list)
    mode: Literal["work", "series", "author", "tag"] = "work"
    download_chapters: bool = True
    save_metadata: bool = True
    export_pdf: bool = False
    export_epub: bool = False
    max_pages: int = 5


TASK_PARAM_MODELS: dict[str, type[BaseModel]] = {
    "like_share_tag": LstParams,
    "author_img": AuthorImgParams,
    "author_txt": AuthorTxtParams,
    "single_img": SingleParams,
    "single_txt": SingleParams,
    "ao3": Ao3Params,
}


class TaskStartPayload(BaseModel):
    type: str
    params: dict[str, Any] = Field(default_factory=dict)

    def validated_params(self) -> dict[str, Any]:
        """按任务类型校验参数；未知类型抛 ValueError（路由层转 400）。"""
        model = TASK_PARAM_MODELS.get(self.type)
        if model is None:
            raise ValueError(f"不支持的任务类型: {self.type}")
        return model(**self.params).model_dump()


# ---------- 配置 / 设置（请求体） ----------


class ConfigPayload(BaseModel):
    login_key: str = ""
    login_auth: str = ""


class SettingsPayload(BaseModel):
    save_path: str | None = None
    auto_dedup: bool | None = None
    notify_on_complete: bool | None = None


class HistoryCheckPayload(BaseModel):
    url: str = ""


# ---------- 响应模型 ----------


class MessageResponse(BaseModel):
    """通用操作结果。"""

    message: str


class ConfigResponse(BaseModel):
    login_key: str
    login_auth: str  # 遮蔽后的授权码
    has_auth: bool
    file_path: str


class SettingsResponse(BaseModel):
    save_path: str
    auto_dedup: bool
    notify_on_complete: bool


class TaskStatusResponse(BaseModel):
    running: bool
    current_task: str | None
    progress: int
    message: str
    logs: list[str]
    error: str | None


class VersionResponse(BaseModel):
    version: str


class FileEntry(BaseModel):
    name: str
    path: str
    size: int
    type: Literal["image", "text"]


class FilesResponse(BaseModel):
    files: list[FileEntry]
    total: int


class HistoryItem(BaseModel):
    id: str
    type: str
    url: str
    title: str
    author: str
    file_path: str
    source: str
    download_time: str
    timestamp: int


class HistoryStats(BaseModel):
    total: int
    images: int
    articles: int


class HistoryQueryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    per_page: int
    total_pages: int
    stats: HistoryStats


class HistoryCheckResponse(BaseModel):
    downloaded: bool
    url: str
