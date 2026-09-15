import { API_BASE } from "./api.js";
import { showNotification } from "./ui.js";

export async function loadConfig() {
  try {
    const res = await fetch(API_BASE + "/api/config");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const ct = res.headers.get("content-type");
    if (!ct || !ct.includes("application/json")) {
      throw new Error("后端未启动");
    }
    const data = await res.json();
    const loginKeyEl = document.getElementById("loginKey");
    if (loginKeyEl) loginKeyEl.value = data.login_key;
    updateAuthStatus(data.has_auth);
  } catch (e) {
    console.error("加载配置失败:", e);
    setTimeout(loadConfig, 2000);
  }
}
export async function saveConfig() {
  const loginKey = document.getElementById("loginKey").value;
  const loginAuth = document.getElementById("loginAuth").value;
  try {
    const res = await fetch(API_BASE + "/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ login_key: loginKey, login_auth: loginAuth }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    if (data.success) {
      showNotification("配置保存成功！", "success");
      loadConfig();
    }
  } catch (e) {
    showNotification("保存失败: " + e.message, "error");
  }
};
function updateAuthStatus(hasAuth) {
  const el = document.getElementById("authStatus");
  if (!el) return;
  if (hasAuth) {
    el.textContent = "已配置";
    el.classList.add("success");
    el.classList.remove("error");
  } else {
    el.textContent = "未配置";
    el.classList.add("error");
    el.classList.remove("success");
  }
}

export async function saveAppSettings() {
  const autoDedup = document.getElementById("autoDedupToggle").checked;
  try {
    await fetch(API_BASE + "/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ auto_dedup: autoDedup }),
    });
  } catch (e) {
    console.error("保存设置失败:", e);
  }
}
export async function loadAppSettings() {
  try {
    const res = await fetch(API_BASE + "/api/settings");
    if (!res.ok) return;
    const data = await res.json();
    const pathEl = document.getElementById("savePath");
    if (pathEl) pathEl.value = data.save_path || "./dir";
    const dedupEl = document.getElementById("autoDedupToggle");
    if (dedupEl) dedupEl.checked = data.auto_dedup !== false;
  } catch (e) {
    console.error("加载设置失败:", e);
  }
}
export async function saveSavePath() {
  const path = document.getElementById("savePath").value.trim() || "./dir";
  try {
    const res = await fetch(API_BASE + "/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ save_path: path }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    showNotification("保存路径已更新", "success");
  } catch (e) {
    showNotification("保存失败: " + e.message, "error");
  }
}
export async function browseSavePath() {
  const isTauri =
    window.__TAURI__ !== undefined || window.__TAURI_INTERNALS__ !== undefined;
  if (isTauri) {
    try {
      let dialog;
      if (window.__TAURI__ && window.__TAURI__.dialog) {
        dialog = window.__TAURI__.dialog;
      } else {
        dialog = await import("@tauri-apps/plugin-dialog");
      }
      const selected = await dialog.open({
        directory: true,
        multiple: false,
        title: "选择保存目录",
      });
      if (selected) {
        document.getElementById("savePath").value = selected;
        showNotification("已选择: " + selected, "success");
      }
    } catch (e) {
      console.error("打开文件夹选择器失败:", e);
      showNotification("请手动输入路径", "info");
    }
  } else {
    showNotification("浏览器模式下请手动输入路径", "info");
  }
}
