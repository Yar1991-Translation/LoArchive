# LoArchive API 契约（v2）

前后端同步重构的对照规范。v2 与 v1（旧版）的差异在文末列出。
除静态资源外所有接口路径以 `/api` 为前缀；交互均为 JSON（SSE 除外）。

## 通用约定

- **成功**：直接返回数据本体，不再包裹 `{"success": true}`。
- **错误**：使用正确的 HTTP 状态码，响应体统一为 `{"detail": <人话错误信息>}`；
  请求体校验失败返回 FastAPI 标准 422（`detail` 为数组）。前端 client 统一归一化为通知。
- **任务模型**：同一时刻只允许一个任务运行（单工作线程，协作式取消）。
- **版本**：`GET /api/version` 返回应用版本，前端展示与更新检查以此为单一来源。

## 配置（Lofter 登录）

### `GET /api/config`
```json
{ "login_key": "LOFTER-PHONE-LOGIN-AUTH", "login_auth": "abcde...vwxyz", "has_auth": true, "file_path": "./dir" }
```
`login_auth` 遮蔽返回（前 5 + ... + 后 5），`has_auth` 表示是否已配置。

### `POST /api/config`
请求体：`{ "login_key": string, "login_auth": string }`
成功 200：`{ "message": "配置已保存" }`

## 应用设置

### `GET /api/settings`
```json
{ "save_path": "./dir", "auto_dedup": true, "notify_on_complete": true }
```
（主题为前端本地偏好，不再走后端。）

### `POST /api/settings`
请求体（全部可选的部分更新）：`{ "save_path"?: string, "auto_dedup"?: boolean, "notify_on_complete"?: boolean }`
成功 200：`{ "message": "设置已保存" }`；保存目录创建失败返回 400。
后端会确保 `save_path` 及其 `img/`、`article/` 子目录存在。

## 任务

### `POST /api/task/start`
请求体：
```json
{ "type": "like_share_tag", "params": { ... } }
```
`type` 与对应 `params` 模型：

| type | params |
|---|---|
| `like_share_tag` | `{ url, mode: "like1"\|"like2"\|"share"\|"tag", save_mode, start_time, export_pdf }` |
| `author_img` | `{ author_url, start_time, end_time }` |
| `author_txt` | `{ author_url }` |
| `single_img` / `single_txt` | `{ urls: string[] }` |
| `ao3` | `{ urls: string[], mode: "work"\|"series"\|"author"\|"tag", download_chapters, save_metadata, export_pdf, export_epub, max_pages }` |

成功 200：`{ "message": "任务已启动" }`；已有任务运行返回 **409**；参数校验失败返回 **422**。

### `GET /api/task/status`（SSE 不可用时的轮询回退）
```json
{ "running": false, "current_task": null, "progress": 100, "message": "", "logs": ["[12:00:00] ..."], "error": null }
```

### `POST /api/task/stop`
设置取消标志，爬虫在下一检查点中断。成功 200：`{ "message": "已请求停止任务" }`。

### `GET /api/task/events`（SSE）
事件流（`data` 均为 JSON 字符串；空闲约 15 秒发送一次 `ping` 心跳）：

| event | data |
|---|---|
| `snapshot` | TaskStatus（订阅后立即推送一次） |
| `log` | `{ "line": "[12:00:00] ...", "message": "..." }` |
| `progress` | `{ "progress": 42 }` |
| `done` | TaskStatus（任务结束，无论成败；失败时 `error` 非空） |
| `ping` | 空 |

## 文件列表

### `GET /api/files`
```json
{ "files": [ { "name": "a.jpg", "path": "img/a.jpg", "size": 10240, "type": "image" } ], "total": 1 }
```
遍历 `save_path`，最多返回 200 条，`type` 为 `image` 或 `text`。

## 下载历史

### `GET /api/history?page=1&per_page=20&type=&source=&search=`
```json
{
  "items": [ { "id": "...", "type": "image", "url": "...", "title": "...", "author": "...",
               "file_path": "...", "source": "lofter", "download_time": "2026-01-01 12:00:00", "timestamp": 1767225600 } ],
  "total": 100, "page": 1, "per_page": 20, "total_pages": 5,
  "stats": { "total": 100, "images": 60, "articles": 40 }
}
```
`type` 过滤值：`image` / `article` / `ao3`；`source`：`lofter` / `ao3`。`per_page` 限制在 10–100。

### `POST /api/history/clear` → `{ "message": "历史记录已清空" }`
### `DELETE /api/history/delete/{item_id}` → `{ "message": "记录已删除" }`；记录不存在返回 **404**
### `POST /api/history/check`
请求体：`{ "url": string }`；返回 `{ "downloaded": bool, "url": string }`（`auto_dedup` 关闭时恒为 `false`）。

## 版本

### `GET /api/version` → `{ "version": "1.2.0-dev.1" }`

## 静态资源

后端在浏览器模式下托管前端构建产物（`frontend/dist`，`html=True` 回退到 index.html）；
非 `/api/*` 响应带 `Cache-Control: no-cache`。Tauri 模式下前端由应用内协议加载，跨域调用本 API。

## v2 相对 v1 的差异

1. 移除 `success` 包装；错误改用 HTTP 状态码 + 统一 `{"detail"}` 错误体。
2. `POST /api/task/start` 任务冲突返回 409（原为 200 + success=false）。
3. `DELETE /api/history/delete/{id}` 记录不存在返回 404（原恒为 200）。
4. `GET/POST /api/settings` 移除 `dark_mode`（主题改由前端本地管理）。
5. 新增 `GET /api/version`。
6. 其余端点请求/响应形状保持不变。
