"""日志配置：控制台 + 数据目录内滚动文件（打包无控制台时文件是唯一出口）。"""

import logging
import logging.handlers
import os

_CONFIGURED = False

LOG_FILENAME = "loarchive.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(data_dir: str | None = None, level: int = logging.INFO) -> None:
    """初始化 loarchive 命名空间的日志；重复调用是空操作。"""
    global _CONFIGURED
    if _CONFIGURED:
        return

    logger = logging.getLogger("loarchive")
    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if data_dir:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                os.path.join(data_dir, LOG_FILENAME),
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError as e:
            logger.warning("无法创建日志文件: %s", e)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """获取 loarchive.<name> 子日志器。"""
    return logging.getLogger(f"loarchive.{name}")
