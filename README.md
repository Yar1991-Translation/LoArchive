# LoArchive

<p align="center">
  <img src="src-tauri/icons/128x128.png" alt="LoArchive Logo" width="128">
</p>

<p align="center">
  <strong>📚 Lofter & AO3 内容存档工具</strong>
</p>

<p align="center">
  一站式保存你喜欢的同人作品
</p>

<p align="center">
  <a href="#-功能特性">功能特性</a> •
  <a href="#-下载安装">下载安装</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-使用说明">使用说明</a> •
  <a href="#-常见问题">常见问题</a>
</p>

---

## ✨ 功能特性

### Lofter 内容爬取

| 功能 | 说明 |
|------|------|
| ❤️ 喜欢/推荐/Tag | 批量保存你点过喜欢、推荐的内容，或 Tag 下的内容 |
| 🖼️ 作者图片 | 下载指定作者发布的所有图片 |
| 📝 作者文章 | 保存指定作者的所有文章和文本 |
| 📎 单篇保存 | 保存单个博客的图片或文章 |

### AO3 文章下载

| 功能 | 说明 |
|------|------|
| 📖 单篇作品 | 下载单个作品的全部章节 |
| 📚 系列作品 | 批量下载整个系列 |
| 👤 作者作品 | 下载某作者的全部作品 |
| 🏷️ Tag 搜索 | 按 Tag 批量下载作品 |

### 导出格式

- **TXT** - 纯文本格式，方便阅读
- **HTML** - 保留格式排版
- **PDF** - 精美排版，支持中文，适合打印

---

## 📥 下载安装

### 方式一：桌面应用（推荐小白用户）

从 [Releases](../../releases) 页面下载最新版本：

| 系统 | 下载文件 |
|------|----------|
| Windows | `LoArchive_x.x.x_x64-setup.exe` |

双击安装即可使用，无需配置环境。

### 方式二：源码运行（推荐开发者）

**环境要求：**
- Python 3.8+
- Node.js 18+ (仅打包桌面应用需要)

```bash
# 克隆项目
git clone https://github.com/你的用户名/LoArchive.git
cd LoArchive

# 安装依赖
pip install -r requirements.txt

# 启动 Web 界面
python web_app.py
```

访问 http://localhost:5000 即可使用。

---

## 🚀 快速开始

### 1️⃣ 配置 Lofter 登录信息

> ⚠️ **AO3 功能无需配置，可直接使用**

Lofter 需要登录后才能访问大部分内容，请按以下步骤获取授权码：

1. 打开 [Lofter](https://www.lofter.com) 并登录
2. 按 `F12` 打开开发者工具
3. 切换到 `Application`（应用程序）标签
4. 左侧选择 `Cookies` → `https://www.lofter.com`
5. 根据你的登录方式找到对应的值：

| 登录方式 | Cookie 名称 |
|---------|-------------|
| 手机号登录 | `LOFTER-PHONE-LOGIN-AUTH` |
| Lofter ID 登录 | `Authorization` |
| QQ/微信/微博登录 | `LOFTER_SESS` |
| 邮箱登录 | `NTES_SESS` |

6. 在应用的「设置」页面填入登录方式和授权码

### 2️⃣ 开始使用

1. 从左侧菜单选择功能
2. 填入要爬取的链接
3. 选择保存选项
4. 点击「开始」按钮
5. 文件保存在 `./dir` 目录下

---

## 📖 使用说明

### Lofter - 喜欢/推荐/Tag

**我的喜欢 / 我的推荐：**
- 链接填写你的个人主页，如 `https://yourname.lofter.com/`
- 可选择只保存某个时间之后的内容

**Tag 内容：**
- 链接填写 Tag 页面，如 `https://www.lofter.com/tag/某tag`
- Tag 链接可选择排序方式：`/new`(最新)、`/total`(总榜)、`/month`(月榜)、`/week`(周榜)、`/date`(日榜)

### Lofter - 作者内容

- 链接填写作者主页，如 `https://authorname.lofter.com/`
- 可设置时间范围筛选

### AO3 下载

- 支持作品、系列、作者、Tag 四种模式
- 可选择是否导出 PDF
- Tag/作者模式可限制最大页数

---

## ❓ 常见问题

<details>
<summary><strong>Q: 为什么 Lofter 爬取失败？</strong></summary>

1. 检查登录信息是否正确配置
2. 授权码可能已过期，请重新获取
3. 确保喜欢/推荐设置为公开可见
</details>

<details>
<summary><strong>Q: 为什么有些内容爬不到？</strong></summary>

- 已被删除或屏蔽的内容无法获取
- Tag 模式有数量限制：最新 1099 条，热度榜 500 条
- 仅自己可见的内容需要使用其他方式
</details>

<details>
<summary><strong>Q: PDF 中文显示为方块？</strong></summary>

请确保系统安装了中文字体。Windows 系统一般不会有此问题。
</details>

<details>
<summary><strong>Q: 如何更新授权码？</strong></summary>

授权码有有效期，过期后需要重新获取。在「设置」页面重新填入新的授权码即可。
</details>

---

## 🛠️ 开发相关

### 项目结构

```
LoArchive/
├── web_app.py          # Flask 后端
├── templates/          # 前端页面
├── static/             # 静态资源
├── src-tauri/          # Tauri 桌面应用
├── l*.py               # 原命令行工具
└── dir/                # 下载内容目录
```

### 构建桌面应用

```bash
# 安装 Node 依赖
npm install

# 开发模式
npm run tauri dev

# 打包发布
npm run tauri build
```

---

## 📜 致谢

本项目基于 [lofterSpider](https://github.com/IshtarTang/lofterSpider) 开发，感谢原作者的开源贡献。

在原项目基础上新增了：
- 现代化 Web GUI 界面
- AO3 下载支持
- PDF 导出功能
- Tauri 桌面应用
- 新手引导功能

---

## 📄 许可证

MIT License

---

<p align="center">
  如果这个工具对你有帮助，欢迎 ⭐ Star 支持！
</p>
