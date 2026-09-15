"""应用配置的加载与保存（单一数据源：配置文件）。"""

import json
import os
import threading

DEFAULT_CONFIG = {
    "login_key": "LOFTER-PHONE-LOGIN-AUTH",
    "login_auth": "",
    "file_path": "./dir",
    "save_path": "./dir",  # 用户自定义保存路径
    "dark_mode": False,
    "auto_dedup": True,  # 自动去重
    "notify_on_complete": True,  # 完成通知
}


class ConfigStore:
    """线程安全的配置存取。"""

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self._config = dict(DEFAULT_CONFIG)
        self.load()

    @property
    def data(self) -> dict:
        """实时配置字典（供爬虫读取）。"""
        return self._config

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value) -> None:
        with self._lock:
            self._config[key] = value

    def update(self, mapping: dict) -> None:
        with self._lock:
            self._config.update(mapping)

    def load(self) -> dict:
        """从文件加载配置（容错：损坏时保留现有配置）。"""
        with self._lock:
            if os.path.exists(self.path):
                try:
                    with open(self.path, encoding="utf-8") as f:
                        saved_config = json.load(f)
                    self._config.update(saved_config)
                except Exception as e:
                    print(f"加载配置文件失败: {e}")
            return self._config

    def save(self) -> None:
        """保存配置到文件。"""
        with self._lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存配置文件失败: {e}")

    def masked_auth(self) -> str:
        """遮蔽后的授权码（用于 API 返回，保持原形状）。"""
        auth = self._config.get("login_auth", "")
        if len(auth) > 10:
            return auth[:5] + "..." + auth[-5:]
        return auth
