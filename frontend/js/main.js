/* LoArchive 前端入口 */
import { initTheme, setTheme } from "./theme.js";
import { initNavigation, initModeCards } from "./navigation.js";
import { initTauri } from "./tauri.js";
import { initContextMenu, initTooltips } from "./ui.js";
import { initOnboarding } from "./onboarding.js";
import {
  loadConfig,
  saveConfig,
  loadAppSettings,
  saveAppSettings,
  saveSavePath,
  browseSavePath,
} from "./settings.js";
import { initDevMode, toggleDevMode } from "./devtools.js";
import {
  startLstTask,
  startAuthorImgTask,
  startAuthorTxtTask,
  startSingleTask,
  startAo3Task,
} from "./tasks.js";
import { loadHistory, clearHistory, copyFilePath, deleteHistoryItem } from "./history.js";
import { checkForUpdates, initUpdateCheck, APP_VERSION } from "./updater.js";

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initNavigation();
  initModeCards();
  initTauri();
  initContextMenu();
  initTooltips();
  initOnboarding();
  loadConfig();
  loadAppSettings();
  initDevMode();
});

// 应用启动后延迟检查更新
initUpdateCheck();

/* HTML 内联事件处理器（onclick / onchange / onkeydown）所需的全局函数 */
Object.assign(window, {
  saveConfig,
  startLstTask,
  startAuthorImgTask,
  startAuthorTxtTask,
  startSingleTask,
  startAo3Task,
  loadHistory,
  clearHistory,
  copyFilePath,
  deleteHistoryItem,
  browseSavePath,
  saveSavePath,
  saveAppSettings,
  toggleDevMode,
  setTheme,
  checkForUpdates,
});
window.APP_VERSION = APP_VERSION;
