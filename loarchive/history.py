"""下载历史的读写、去重、分页查询（线程安全）。"""

import json
import os
import threading
import time

MAX_HISTORY_ITEMS = 1000


def compute_stats(items: list) -> dict:
    """从 items 列表实时计算统计。"""
    total = len(items)
    images = sum(1 for i in items if i.get("type") == "image")
    articles = sum(1 for i in items if i.get("type") in ("article", "ao3"))
    return {"total": total, "images": images, "articles": articles}


class HistoryManager:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()

    def load(self) -> dict:
        """加载下载历史。"""
        default_history = {"items": []}
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    data = json.load(f)
                    if "items" not in data:
                        data["items"] = []
                    return data
            except Exception as e:
                print(f"加载历史记录失败: {e}")
                return default_history
        return default_history

    def save(self, history: dict) -> None:
        """保存下载历史。"""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def add(self, item_type, url, title, author, file_path, source="lofter") -> bool:
        """添加到下载历史（按 URL 去重，保留最近 1000 条）。"""
        with self._lock:
            history = self.load()

            for item in history["items"]:
                if item.get("url") == url:
                    return False

            record = {
                "id": f"{int(time.time() * 1000)}-{os.urandom(4).hex()}",
                "type": item_type,  # 'image', 'article', 'ao3'
                "url": url,
                "title": title or "无标题",
                "author": author or "未知作者",
                "file_path": file_path,
                "source": source,
                "download_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": int(time.time()),
            }

            history["items"].insert(0, record)

            if len(history["items"]) > MAX_HISTORY_ITEMS:
                history["items"] = history["items"][:MAX_HISTORY_ITEMS]

            self.save(history)
            return True

    def is_downloaded(self, url: str) -> bool:
        """检查 URL 是否已下载过。"""
        with self._lock:
            history = self.load()
            return any(item.get("url") == url for item in history["items"])

    def clear(self) -> bool:
        """清空下载历史。"""
        with self._lock:
            self.save({"items": []})
        return True

    def delete(self, item_id: str) -> None:
        """删除单条历史记录。"""
        with self._lock:
            history = self.load()
            history["items"] = [i for i in history["items"] if i.get("id") != item_id]
            self.save(history)

    def query(
        self, page: int = 1, per_page: int = 20, filter_type: str = "", filter_source: str = "", search: str = ""
    ) -> dict:
        """分页 + 过滤 + 搜索查询（API 形状与原实现一致）。"""
        with self._lock:
            history = self.load()
            items = history["items"]

            page = max(1, page)
            per_page = min(100, max(10, per_page))

            if filter_type:
                items = [i for i in items if i.get("type") == filter_type]
            if filter_source:
                items = [i for i in items if i.get("source") == filter_source]
            if search:
                search_lower = search.lower()
                items = [
                    i
                    for i in items
                    if search_lower in i.get("title", "").lower()
                    or search_lower in i.get("author", "").lower()
                    or search_lower in i.get("url", "").lower()
                ]

            stats = compute_stats(items)

            total = len(items)
            total_pages = max(1, (total + per_page - 1) // per_page)
            page = min(page, total_pages)
            start = (page - 1) * per_page
            items = items[start : start + per_page]

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "stats": stats,
            }
