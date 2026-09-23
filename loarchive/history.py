"""下载历史存储：SQLite 单文件，含旧版 JSON 的自动迁移。

同进程内可能被工作线程与 API 线程并发访问，统一经 RLock 串行化；
连接常驻（check_same_thread=False），写入由锁保证互斥。
"""

import json
import os
import sqlite3
import threading
import time

from .logsetup import get_logger

logger = get_logger("history")

MAX_HISTORY_ITEMS = 1000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    file_path TEXT NOT NULL,
    source TEXT NOT NULL,
    download_time TEXT NOT NULL,
    timestamp INTEGER NOT NULL
);
"""

_SELECT_COLUMNS = "id, type, url, title, author, file_path, source, download_time, timestamp"


def compute_stats(items: list) -> dict:
    """从 items 列表实时计算统计（保留给纯函数测试与外部调用）。"""
    total = len(items)
    images = sum(1 for i in items if i.get("type") == "image")
    articles = sum(1 for i in items if i.get("type") in ("article", "ao3"))
    return {"total": total, "images": images, "articles": articles}


def _row_to_item(row: tuple) -> dict:
    return {
        "id": row[0],
        "type": row[1],
        "url": row[2],
        "title": row[3],
        "author": row[4],
        "file_path": row[5],
        "source": row[6],
        "download_time": row[7],
        "timestamp": row[8],
    }


class HistoryManager:
    """SQLite 版下载历史：增删查、URL 去重、分页过滤统计。"""

    def __init__(self, db_path: str, legacy_json_path: str | None = None):
        self.path = db_path
        self.legacy_json_path = legacy_json_path
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(os.path.abspath(db_path)) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(_SCHEMA)
        self._conn.commit()
        self._migrate_legacy_json()

    # ---------- 旧 JSON 迁移 ----------

    def _migrate_legacy_json(self) -> int:
        """把旧版 download_history.json 合并导入 SQLite，成功后把源文件改名备份。

        合并按 URL 去重（INSERT OR IGNORE），因此重复执行安全；改名避免
        clear() 之后下次启动又被重新导入。
        """
        path = self.legacy_json_path
        if not path or not os.path.exists(path):
            return 0

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            items = data.get("items", [])
        except Exception as e:
            logger.warning("旧历史文件无法解析，跳过迁移 %s: %s", path, e)
            return 0

        imported = 0
        with self._lock:
            # JSON 内列表最新在前，倒序插入使最新记录拥有最大 rowid
            for record in reversed(items):
                if not isinstance(record, dict) or not record.get("url"):
                    continue
                cursor = self._conn.execute(
                    f"INSERT OR IGNORE INTO history ({_SELECT_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(record.get("id") or f"{int(time.time() * 1000)}-{os.urandom(4).hex()}"),
                        record.get("type") or "article",
                        record["url"],
                        record.get("title") or "无标题",
                        record.get("author") or "未知作者",
                        record.get("file_path") or "",
                        record.get("source") or "lofter",
                        record.get("download_time") or time.strftime("%Y-%m-%d %H:%M:%S"),
                        int(record.get("timestamp") or int(time.time())),
                    ),
                )
                imported += cursor.rowcount
            self._conn.commit()
            self._enforce_capacity()

        try:
            os.replace(path, path + ".bak")
            logger.info("旧历史文件已迁移 %d 条并备份为 %s.bak", imported, path)
        except OSError as e:
            logger.warning("旧历史文件迁移后改名失败（下次启动会重新合并）: %s", e)

        if imported:
            logger.info("已从旧 JSON 导入 %d 条下载历史", imported)
        return imported

    # ---------- 写入 ----------

    def _enforce_capacity(self) -> None:
        self._conn.execute(
            "DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY rowid DESC LIMIT ?)",
            (MAX_HISTORY_ITEMS,),
        )

    def add(self, item_type, url, title, author, file_path, source="lofter") -> bool:
        """添加到下载历史（按 URL 去重，容量上限 MAX_HISTORY_ITEMS）。"""
        with self._lock:
            cursor = self._conn.execute(
                f"INSERT OR IGNORE INTO history ({_SELECT_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"{int(time.time() * 1000)}-{os.urandom(4).hex()}",
                    item_type,
                    url,
                    title or "无标题",
                    author or "未知作者",
                    file_path,
                    source,
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    int(time.time()),
                ),
            )
            self._conn.commit()
            if cursor.rowcount == 0:
                return False
            self._enforce_capacity()
            self._conn.commit()
            return True

    def is_downloaded(self, url: str) -> bool:
        """检查 URL 是否已下载过。"""
        with self._lock:
            row = self._conn.execute("SELECT 1 FROM history WHERE url = ? LIMIT 1", (url,)).fetchone()
            return row is not None

    def clear(self) -> bool:
        """清空下载历史。"""
        with self._lock:
            self._conn.execute("DELETE FROM history")
            self._conn.commit()
        return True

    def delete(self, item_id: str) -> bool:
        """删除单条历史记录；返回是否存在并被删除。"""
        with self._lock:
            cursor = self._conn.execute("DELETE FROM history WHERE id = ?", (item_id,))
            self._conn.commit()
            return cursor.rowcount > 0

    # ---------- 查询 ----------

    def _filtered_stats(self, conditions: list, params: list) -> dict:
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self._conn.execute(f"SELECT type, COUNT(*) FROM history{where} GROUP BY type", params).fetchall()
        counts = {row[0]: row[1] for row in rows}
        total = sum(counts.values())
        return {
            "total": total,
            "images": counts.get("image", 0),
            "articles": counts.get("article", 0) + counts.get("ao3", 0),
        }

    def query(
        self, page: int = 1, per_page: int = 20, filter_type: str = "", filter_source: str = "", search: str = ""
    ) -> dict:
        """分页 + 过滤 + 搜索查询（API 形状与旧版一致）。"""
        with self._lock:
            page = max(1, page)
            per_page = min(100, max(10, per_page))

            conditions: list[str] = []
            params: list = []
            if filter_type:
                conditions.append("type = ?")
                params.append(filter_type)
            if filter_source:
                conditions.append("source = ?")
                params.append(filter_source)
            if search:
                # LIKE 的 % _ 与转义符本身按字面匹配
                escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                pattern = f"%{escaped}%"
                conditions.append("(title LIKE ? ESCAPE '\\' OR author LIKE ? ESCAPE '\\' OR url LIKE ? ESCAPE '\\')")
                params.extend([pattern, pattern, pattern])

            where = f" WHERE {' AND '.join(conditions)}" if conditions else ""

            total = self._conn.execute(f"SELECT COUNT(*) FROM history{where}", params).fetchone()[0]
            stats = self._filtered_stats(conditions, params)

            total_pages = max(1, (total + per_page - 1) // per_page)
            page = min(page, total_pages)
            offset = (page - 1) * per_page

            rows = self._conn.execute(
                f"SELECT {_SELECT_COLUMNS} FROM history{where} ORDER BY rowid DESC LIMIT ? OFFSET ?",
                [*params, per_page, offset],
            ).fetchall()

            return {
                "items": [_row_to_item(row) for row in rows],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "stats": stats,
            }

    def close(self) -> None:
        with self._lock:
            self._conn.close()
