<p align="center">
  <img src="src-tauri/icons/128x128.png" alt="LoArchive" width="128">
</p>

<h1 align="center">LoArchive</h1>

<p align="center">
  一站式保存你喜欢的同人作品<br>
  支持 Lofter 与 AO3 的内容存档工具
</p>

<p align="center">
  <a href="https://github.com/Yar1991-Translation/LoArchive/releases"><img alt="Release" src="https://img.shields.io/github/v/release/Yar1991-Translation/LoArchive?display_name=tag&amp;sort=semver"></a>
  <a href="https://github.com/Yar1991-Translation/LoArchive/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/Yar1991-Translation/LoArchive/actions/workflows/test.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-3776ab">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows-0078d4">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-2ea44f">
</p>

---

## 简介

LoArchive 是一个在本机运行的图形化存档工具，用于把 Lofter 与 AO3 上的作品保存到本地。提供安装版桌面应用，也可以直接从源码启动 Web 界面。

所有抓取、解析与导出都在本地完成，不需要上传任何数据，也不依赖第三方服务。

## 架构

```mermaid
flowchart LR
    UI["前端<br/>原生 ES Modules"] -->|HTTP / SSE| API["FastAPI 后端"]
    API --> SP["爬虫<br/>Lofter / AO3"]
    SP --> EX["导出<br/>TXT / PDF / EPUB"]
    SP --> FS[("本地存档目录")]
    T["Tauri 桌面壳"] -.->|启动 sidecar| API
```

- 前端为无构建步骤的原生 ES Modules，由后端直接托管
- 后端为 FastAPI 应用，任务以工作线程执行，日志与进度通过 SSE 实时推送
- 桌面版由 Tauri 启动内嵌的 Python sidecar，并提供原生窗口与文件夹选择器

## 功能特性

### Lofter

| 功能 | 说明 |
| --- | --- |
| 喜欢 / 推荐 / Tag | 批量保存点过喜欢、推荐的内容，或指定 Tag 下的内容 |
| 他人喜欢 | 抓取其他用户公开的喜欢列表 |
| 作者图片 | 下载指定作者发布的所有图片 |
| 作者文章 | 保存指定作者的全部文章 |
| 单篇保存 | 保存单篇博客的图片或文章 |

### AO3

| 功能 | 说明 |
| --- | --- |
| 单篇作品 | 下载作品的全部章节 |
| 系列作品 | 批量下载整个系列 |
| 作者作品 | 下载某位作者的全部作品 |
| Tag 搜索 | 按 Tag 批量下载作品，可限制抓取页数 |

### 导出格式

| 格式 | 说明 |
| --- | --- |
| TXT | 始终保存，纯文本便于阅读与检索 |
| PDF | 书籍式排版、支持中文，Lofter 与 AO3 均可导出 |
| EPUB | 支持分章目录，仅 AO3 提供 |
| HTML | 导出 PDF 时一并保留的中间产物，便于自行调整排版 |

## 下载安装

### 方式一：桌面应用

从 [Releases](https://github.com/Yar1991-Translation/LoArchive/releases) 页面下载最新安装包：

| 系统 | 下载文件 |
| --- | --- |
| Windows | `LoArchive_<版本>_x64-setup.exe` |

双击安装即可使用，无需自行配置 Python 或 Node 环境。桌面版目前仅提供 Windows 安装包。

### 方式二：源码运行

环境要求：Python 3.11 及以上。Node.js 仅打包桌面应用时需要（18 及以上）。

```bash
git clone https://github.com/Yar1991-Translation/LoArchive.git
cd LoArchive

pip install -r requirements.txt
python run.py
```

启动后访问 <http://localhost:5000> 即可使用。

## 快速开始

### 配置 Lofter 授权码

AO3 相关功能无需配置，可直接使用。Lofter 需要登录后才能访问大部分内容，按以下步骤获取授权码：

1. 打开 [Lofter](https://www.lofter.com) 并登录
2. 按 `F12` 打开开发者工具，切换到 `Application`（应用程序）标签
3. 左侧选择 `Cookies`，展开 `https://www.lofter.com`
4. 按下表找到你所用登录方式对应的值，复制完整内容

| 登录方式 | Cookie 名称 |
| --- | --- |
| 手机号登录 | `LOFTER-PHONE-LOGIN-AUTH` |
| Lofter ID 登录 | `Authorization` |
| QQ / 微信 / 微博登录 | `LOFTER_SESS` |
| 邮箱登录 | `NTES_SESS` |

5. 在应用的「设置」页面选择登录方式，粘贴授权码并保存

### 开始存档

1. 从左侧菜单选择功能模块
2. 填入要抓取的链接
3. 勾选需要的保存选项
4. 点击「开始」按钮，进度与日志会实时显示在右侧
5. 内容保存在存档目录中，同时记入「下载历史」

## 使用说明

### Lofter 喜欢 / 推荐 / Tag

| 模式 | 链接填法 |
| --- | --- |
| 我的喜欢 | 个人主页，如 `https://yourname.lofter.com/` |
| 我的推荐 / 他人喜欢 | 对应的用户主页 |
| Tag 内容 | Tag 页面，如 `https://www.lofter.com/tag/某tag` |

Tag 链接可带排序后缀：`/new`（最新）、`/total`（总榜）、`/month`（月榜）、`/week`（周榜）、`/date`（日榜）。喜欢、推荐与 Tag 模式可选择只保存某个时间之后的内容。

### Lofter 作者内容

链接填写作者主页，如 `https://authorname.lofter.com/`。作者图片与作者文章分别对应两个面板，均可设置时间范围筛选。

### AO3 下载

链接填写作品、系列、作者作品页或 Tag 作品页的地址，支持一次粘贴多个链接（每行一个）。作者与 Tag 模式可限制最大抓取页数，并可选择是否下载全部章节、是否保存元数据。

## 项目结构

```text
LoArchive/
├── run.py                    启动入口
├── loarchive/                FastAPI 后端包
│   ├── main.py               应用工厂与 uvicorn 入口
│   ├── config.py             配置读写
│   ├── history.py            下载历史
│   ├── state.py              任务管理（线程、取消标志、SSE 事件）
│   ├── schemas.py            请求参数校验
│   ├── routers/              API 路由
│   ├── spiders/              爬虫实现
│   └── exporters/            PDF / EPUB 导出
├── frontend/                 原生 ES Modules 前端
│   ├── index.html
│   ├── css/main.css
│   └── js/                   按职责拆分的模块
├── scripts/                  构建与校验脚本
├── src-tauri/                Tauri 桌面应用
├── tests/                    pytest 测试
└── dir/                      默认存档目录
```

## 开发

### 常用命令

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 启动后端（开发模式）
python run.py

# 代码检查与格式检查
ruff check .
ruff format --check .

# 运行测试
pytest

# 校验前端模块导入图（前端无打包器，用于捕获缺失导出导致的空白页）
node scripts/check_esm.mjs
```

### 构建桌面应用

```bash
# 安装 Node 依赖
npm install

# 先构建后端 sidecar，再打包
python scripts/build_backend.py
npm run tauri:build
```

如需调试桌面窗口，先启动后端，再另开一个终端运行 `npm run tauri:dev`。

## 后端接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET / POST | `/api/config` | 读取或保存 Lofter 登录信息（读取时授权码遮蔽返回） |
| GET / POST | `/api/settings` | 读取或保存存档路径与开关项 |
| POST | `/api/task/start` | 启动任务，参数按任务类型校验 |
| GET | `/api/task/status` | 轮询任务状态（SSE 不可用时回退） |
| GET | `/api/task/events` | SSE 实时推送日志与进度 |
| POST | `/api/task/stop` | 请求停止当前任务 |
| GET | `/api/files` | 列出已下载文件 |
| GET | `/api/history` | 分页查询下载历史，支持类型、来源与关键词过滤 |
| POST | `/api/history/clear` | 清空下载历史 |
| DELETE | `/api/history/delete/{id}` | 删除单条历史记录 |
| POST | `/api/history/check` | 检查某个链接是否已下载 |

应用运行时访问 <http://localhost:5000/docs> 可查看交互式接口文档。

## 数据存储位置

| 运行方式 | 位置 |
| --- | --- |
| 源码运行 | 项目根目录下的 `loarchive_config.json` 与 `download_history.json` |
| 桌面版 | 用户数据目录，Windows 为 `%APPDATA%\LoArchive` |

桌面版首次启动时，如果安装目录旁存在旧版配置，会自动导入到用户数据目录，且不会覆盖已有数据。

## 常见问题

<details>
<summary>为什么 Lofter 抓取失败？</summary>

1. 检查登录信息是否已正确配置
2. 授权码有有效期，过期后需要在「设置」页面重新获取并填入
3. 确认喜欢 / 推荐列表为公开可见

</details>

<details>
<summary>为什么有些内容抓不到？</summary>

已被删除或屏蔽的内容无法获取；仅自己可见的内容也不在此工具的抓取范围内。

</details>

<details>
<summary>文件保存到哪里了？</summary>

保存在「设置」页面配置的存档目录中，按来源与作者分子目录存放，默认目录为项目下的 `dir/`。历史记录中可以直接复制单个文件的路径。

</details>

<details>
<summary>PDF 中文显示为方块怎么办？</summary>

请确保系统安装了中文字体。Windows 系统一般不会遇到此问题。

</details>

<details>
<summary>如何更新授权码？</summary>

在「设置」页面填入新的登录方式与授权码并保存即可，无需修改任何文件。

</details>

## 已知限制

- 导出的 PDF 不含页码：当前 xhtml2pdf 版本不支持 `@page` 内的页码框（`@bottom-center`），加入会导致导出失败
- Lofter Tag 抓取上限为最新 1099 条、热度榜 500 条
- 喜欢 / 推荐 / Tag 模式单次最多抓取 500 条
- 桌面版目前只提供 Windows 安装包，未提供 macOS 与 Linux 构建

## 致谢

本项目基于 [lofterSpider](https://github.com/IshtarTang/lofterSpider) 开发，感谢原作者的开源贡献。在原项目基础上新增了现代化 Web 界面、AO3 下载、PDF / EPUB 导出、Tauri 桌面应用与新手引导等功能。

## 许可证

本项目以 MIT 许可证发布。

<p align="center">
  如果这个工具对你有帮助，欢迎 Star 支持
</p>
