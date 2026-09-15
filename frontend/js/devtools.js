import { mi } from "./icons.js";
import { API_BASE } from "./api.js";
import { AppState } from "./state.js";
import { switchPanel } from "./navigation.js";
import { startTask } from "./tasks.js";
import { setTheme, THEMES } from "./theme.js";
import { showNotification } from "./ui.js";
import { checkForUpdates, APP_VERSION } from "./updater.js";

/* ========== 开发者模式 ========== */
let devMode = false;
const PANELS = {
  lst: "喜欢/推荐/Tag",
  "author-img": "作者图片",
  "author-txt": "作者文章",
  single: "单篇保存",
  ao3: "AO3文章",
  history: "下载历史",
  settings: "设置",
};
const LST_MODES = {
  like2: "我的喜欢",
  share: "我的推荐",
  tag: "Tag内容",
  like1: "他人喜欢",
};
const SINGLE_MODES = { img: "保存图片", txt: "保存文章" };
const AO3_MODES = {
  work: "单篇作品",
  series: "系列",
  author: "作者",
  tag: "Tag",
};

export function initDevMode() {
  const saved = localStorage.getItem("loarchive_dev_mode");
  if (saved === "true") enableDevMode(false);
}

export function toggleDevMode() {
  const toggle = document.getElementById("devModeToggle");
  if (toggle.checked) enableDevMode(true);
  else disableDevMode();
}

export function enableDevMode(save) {
  devMode = true;
  const toggle = document.getElementById("devModeToggle");
  if (toggle) toggle.checked = true;
  const help = document.getElementById("devModeHelp");
  if (help) help.style.display = "block";

  // 创建底部指示器
  let indicator = document.getElementById("devIndicator");
  if (!indicator) {
    indicator = document.createElement("div");
    indicator.id = "devIndicator";
    indicator.className = "dev-indicator";
    indicator.innerHTML = '<span class="dev-dot"></span> DEV';
    document.body.appendChild(indicator);
  }

  if (save) localStorage.setItem("loarchive_dev_mode", "true");

  // 暴露 dev API 到全局
  window.dev = {
    // 帮助
    help() {
      const cmds = [
        "%cLoArchive Developer Console",
        "",
        "%c=== 面板控制 ===",
        "dev.switchPanel(id)     — 切换面板: " + Object.keys(PANELS).join(", "),
        "dev.listPanels()        — 列出所有面板",
        "dev.currentPanel()      — 当前面板",
        "",
        "%c=== 模式控制 ===",
        "dev.setMode(mode)       — 设置LST模式: " +
          Object.keys(LST_MODES).join(", "),
        "dev.setSingleMode(m)    — 设置单篇模式: " +
          Object.keys(SINGLE_MODES).join(", "),
        "dev.setAo3Mode(m)       — 设置AO3模式: " +
          Object.keys(AO3_MODES).join(", "),
        "dev.listModes()         — 列出所有模式",
        "",
        "%c=== 任务控制 ===",
        "dev.startTask(type)     — 启动任务(使用当前面板的默认参数)",
        "dev.stopTask()          — 停止当前任务",
        "dev.fillUrl(url)        — 填入链接到当前面板",
        "dev.fillTestUrl()       — 填入测试链接",
        "",
        "%c=== UI 测试 ===",
        "dev.toggleDark()        — 切换深色模式",
        "dev.setTheme(name)      — 设置主题: light, dark, bw",
        "dev.listThemes()        — 列出所有主题",
        "dev.notify(msg, type)   — 显示通知(info|success|error|warning)",
        "dev.checkUpdate()       — 检查更新",
        "",
        "%c=== 系统信息 ===",
        "dev.state()             — 应用状态",
        "dev.testApi()           — 测试后端API",
        "dev.getHistory(page)    — 获取下载历史",
        "dev.getConfig()         — 获取配置",
        "",
      ];
      console.log(
        cmds.join("\n"),
        "font-size:16px;font-weight:bold;color:#00bcd4",
        "color:#00bcd4;font-weight:bold",
        "color:#aaa",
        "color:#aaa",
        "color:#aaa",
        "color:#aaa",
      );
      return mi("check_circle") + " 命令列表已输出到控制台";
    },

    // 面板
    switchPanel(id) {
      if (!PANELS[id])
        return console.error("未知面板:", id, "可用:", Object.keys(PANELS));
      switchPanel(id);
      return mi("check_circle") + ` 已切换到: ${PANELS[id]}`;
    },
    listPanels() {
      console.table(PANELS);
      return PANELS;
    },
    currentPanel() {
      return { id: AppState.currentPanel, name: PANELS[AppState.currentPanel] };
    },

    // 模式
    setMode(m) {
      if (!LST_MODES[m])
        return console.error(
          "未知LST模式:",
          m,
          "可用:",
          Object.keys(LST_MODES),
        );
      document.querySelectorAll("[data-mode]").forEach((c) => {
        c.classList.toggle("selected", c.dataset.mode === m);
      });
      AppState.currentMode = m;
      return mi("check_circle") + ` LST模式: ${LST_MODES[m]}`;
    },
    setSingleMode(m) {
      if (!SINGLE_MODES[m]) return console.error("未知单篇模式:", m);
      document.querySelectorAll("[data-single-mode]").forEach((c) => {
        c.classList.toggle("selected", c.dataset.singleMode === m);
      });
      AppState.currentSingleMode = m;
      return mi("check_circle") + ` 单篇模式: ${SINGLE_MODES[m]}`;
    },
    setAo3Mode(m) {
      if (!AO3_MODES[m]) return console.error("未知AO3模式:", m);
      document.querySelectorAll("[data-ao3-mode]").forEach((c) => {
        c.classList.toggle("selected", c.dataset.ao3Mode === m);
      });
      AppState.currentAo3Mode = m;
      return mi("check_circle") + ` AO3模式: ${AO3_MODES[m]}`;
    },
    listModes() {
      console.log("LST模式:", LST_MODES);
      console.log("单篇模式:", SINGLE_MODES);
      console.log("AO3模式:", AO3_MODES);
      return { lst: LST_MODES, single: SINGLE_MODES, ao3: AO3_MODES };
    },

    // 任务
    startTask(type) {
      const panel = AppState.currentPanel;
      if (!type)
        type =
          panel === "ao3"
            ? "ao3"
            : panel === "single"
              ? AppState.currentSingleMode === "img"
                ? "single_img"
                : "single_txt"
              : panel === "author-img"
                ? "author_img"
                : panel === "author-txt"
                  ? "author_txt"
                  : "like_share_tag";
      const urls = {
        ao3: "https://archiveofourown.org/works/12345678",
        single: "https://用户名.lofter.com/post/xxx",
        "author-img": "https://用户名.lofter.com/",
        lst: "https://用户名.lofter.com/",
      };
      const url = urls[panel] || urls["lst"];
      console.log(mi("rocket_launch") + ` 启动任务: ${type}`);
      return startTask(type, {
        url,
        urls: [url],
        mode: AppState.currentMode,
        author_url: url,
      });
    },
    stopTask() {
      fetch(API_BASE + "/api/task/stop", { method: "POST" });
      return "⏹️ 已发送停止请求";
    },
    fillUrl(url) {
      const map = {
        lst: "lstUrl",
        "author-img": "authorImgUrl",
        "author-txt": "authorTxtUrl",
        single: "singleUrls",
        ao3: "ao3Urls",
      };
      const elId = map[AppState.currentPanel];
      if (!elId) return "当前面板没有链接输入框";
      const el = document.getElementById(elId);
      if (!el) return "找不到输入框: " + elId;
      el.value = url;
      return mi("check_circle") + ` 已填入: ${url}`;
    },
    fillTestUrl() {
      const urls = {
        lst: "https://test-user.lofter.com/",
        "author-img": "https://test-user.lofter.com/",
        "author-txt": "https://test-user.lofter.com/",
        single: "https://test-user.lofter.com/post/12345",
        ao3: "https://archiveofourown.org/works/12345678",
      };
      return this.fillUrl(urls[AppState.currentPanel] || urls.lst);
    },

    // UI
    toggleDark() {
      setTheme(
        document.body.classList.contains("dark-mode") ? "light" : "dark",
      );
      return document.body.classList.contains("dark-mode")
        ? mi("dark_mode") + " 深色模式"
        : mi("light_mode") + " 浅色模式";
    },
    setTheme(name) {
      setTheme(name);
      return mi("palette") + " 主题: " + (THEMES[name]?.label || name);
    },
    listThemes() {
      console.table(THEMES);
      return THEMES;
    },
    notify(msg, type) {
      showNotification(msg || "测试通知", type || "info");
      return mi("check_circle") + ` 通知: ${msg}`;
    },
    checkUpdate() {
      checkForUpdates(false);
      return mi("search") + " 检查中...";
    },

    // 系统
    state() {
      const s = { ...AppState, devMode, version: APP_VERSION };
      console.table(s);
      return s;
    },
    async testApi() {
      try {
        const res = await fetch(API_BASE + "/api/config");
        const data = await res.json();
        console.log(mi("check_circle") + " API 连接成功:", data);
        return data;
      } catch (e) {
        console.error(mi("error") + " API 连接失败:", e);
        return null;
      }
    },
    async getHistory(page) {
      try {
        const res = await fetch(`${API_BASE}/api/history?page=${page || 1}`);
        const data = await res.json();
        console.table(data.items);
        return data;
      } catch (e) {
        console.error(mi("error") + " 获取历史失败:", e);
        return null;
      }
    },
    async getConfig() {
      try {
        const res = await fetch(API_BASE + "/api/config");
        const data = await res.json();
        console.table(data);
        return data;
      } catch (e) {
        console.error(mi("error") + " 获取配置失败:", e);
        return null;
      }
    },
  };

  showNotification(
    mi("build") + " 开发者模式已启用 — 在控制台输入 dev.help() 查看命令",
    "info",
    5000,
  );
  console.log(
    "%c" + mi("build") + " 开发者模式已启用 — 输入 dev.help() 查看所有命令",
    "color:#00bcd4;font-size:14px;font-weight:bold",
  );
}

export function disableDevMode() {
  devMode = false;
  localStorage.removeItem("loarchive_dev_mode");
  const help = document.getElementById("devModeHelp");
  if (help) help.style.display = "none";
  const indicator = document.getElementById("devIndicator");
  if (indicator) indicator.remove();
  delete window.dev;
  showNotification("开发者模式已关闭", "info");
}
