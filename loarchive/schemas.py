"""API 请求体的 Pydantic 模型（按任务类型校验参数）。"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------- 任务参数模型 ----------


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
        """按任务类型校验参数；未知类型原样返回（由任务层记录日志）。"""
        model = TASK_PARAM_MODELS.get(self.type)
        if model is None:
            return self.params
        return model(**self.params).model_dump()


# ---------- 配置 / 设置 ----------


class ConfigPayload(BaseModel):
    login_key: str = ""
    login_auth: str = ""


class SettingsPayload(BaseModel):
    save_path: str | None = None
    dark_mode: bool | None = None
    auto_dedup: bool | None = None
    notify_on_complete: bool | None = None


class HistoryCheckPayload(BaseModel):
    url: str = ""
