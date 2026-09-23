"""应用异常层级：让错误处理有类型可依，而不是裸 except Exception。

- ConfigError: 配置缺失或非法（如未配置 Lofter 登录授权码）
- FetchError: 网络请求失败（超时、连接错误、非预期 HTTP 状态）
- ParseError: 页面 / DWR 响应解析失败（对方页面结构变化等）
- TaskCancelled: 任务在检查点发现取消标志（由 TaskManager 捕获，属正常流程）
"""


class LoArchiveError(Exception):
    """LoArchive 基础异常。"""


class ConfigError(LoArchiveError):
    """配置缺失或非法。"""


class FetchError(LoArchiveError):
    """网络请求失败。"""


class ParseError(LoArchiveError):
    """页面或接口响应解析失败。"""


class TaskCancelled(LoArchiveError):
    """爬虫在检查点发现取消标志后抛出，用于中断任务。"""
