import { showNotification } from "./ui.js";

/* 主题切换功能 */
export const THEMES = {
  light: { label: "默认", class: "" },
  dark: { label: "深色", class: "dark-mode" },
  bw: { label: "黑白块", class: "bw-mode" },
};

export function initTheme() {
  const saved = localStorage.getItem("loarchive_theme") || "light";
  applyTheme(saved, false);
}

export function setTheme(name) {
  if (!THEMES[name]) return;
  applyTheme(name, true);
}

export function applyTheme(name, notify) {
  // 清除所有主题 class
  document.body.classList.remove("dark-mode", "bw-mode");
  // 应用新主题
  const theme = THEMES[name];
  if (theme.class) document.body.classList.add(theme.class);
  // 更新选择卡片
  document.querySelectorAll("#themeCards .theme-card").forEach((c) => {
    c.classList.toggle("selected", c.dataset.theme === name);
  });
  // 持久化
  localStorage.setItem("loarchive_theme", name);
  if (notify) showNotification("已切换到" + theme.label + "主题", "success");
}