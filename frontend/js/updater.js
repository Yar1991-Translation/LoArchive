import { mi } from "./icons.js";
import { escapeHtml, showNotification } from "./ui.js";

/* ========== 自动更新功能（GitHub API） ========== */
export const APP_VERSION = "1.2.0-dev.1";
const GITHUB_REPO = "Yar1991-Translation/LoArchive";
let latestRelease = null;

export async function checkForUpdates(silent = false) {
  try {
    if (!silent) showNotification("正在检查更新...", "info");

    const res = await fetch(
      `https://api.github.com/repos/${GITHUB_REPO}/releases/latest`,
    );
    if (!res.ok) {
      if (res.status === 404) {
        if (!silent) showNotification("暂无发布版本", "info");
        return;
      }
      throw new Error("GitHub API 请求失败");
    }

    const release = await res.json();
    latestRelease = release;
    const latestVersion = release.tag_name.replace(/^v/, "");

    if (isNewerVersion(latestVersion, APP_VERSION)) {
      showUpdateNotification(release, latestVersion);
    } else {
      if (!silent)
        showNotification(
          `当前已是最新版本 v${APP_VERSION} "+mi('check_circle')+"`,
          "success",
        );
    }
  } catch (e) {
    console.error("检查更新失败:", e);
    if (!silent) showNotification("检查更新失败，请检查网络连接", "error");
  }
}

export function isNewerVersion(latest, current) {
  // 比较主版本号数字部分，忽略 -dev.1 / -beta.1 这类 pre-release 后缀，
  // 否则 dev 构建无法识别同版本的正式发布（"1.2.0" 应被视为新于 "1.2.0-dev.1"）。
  const numericParts = (version) => version.split("-")[0].split("+")[0].split(".").map(Number);
  const l = numericParts(latest);
  const c = numericParts(current);
  for (let i = 0; i < Math.max(l.length, c.length); i++) {
    if ((l[i] || 0) > (c[i] || 0)) return true;
    if ((l[i] || 0) < (c[i] || 0)) return false;
  }
  return false;
}

export function showUpdateNotification(release, newVersion) {
  const container = document.getElementById("toastContainer");
  const msiAsset = release.assets.find((a) => a.name.endsWith(".msi"));
  const exeAsset = release.assets.find((a) => a.name.endsWith("-setup.exe"));
  const downloadUrl =
    msiAsset?.browser_download_url ||
    exeAsset?.browser_download_url ||
    release.html_url;

  const summary = release.body
    ? release.body
        .split("\n")
        .filter((l) => l.trim() && !l.startsWith("#"))
        .slice(0, 3)
        .join("\n")
    : "";

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `
        <span class="toast-icon"><span class="mi">celebration</span></span>
        <div class="toast-body">
            <div class="toast-title">发现新版本 v${newVersion}</div>
            <div class="toast-text" style="white-space:pre-line;">${escapeHtml(summary || "点击查看更新详情")}</div>
            <div class="toast-actions">
                <button class="toast-btn primary" data-action="download"><span class="mi">download</span> 下载</button>
                <button class="toast-btn secondary" data-action="github"><span class="mi">open_in_new</span> GitHub</button>
                <button class="toast-btn secondary" data-action="dismiss">忽略</button>
            </div>
        </div>
        <button class="toast-close"><span class="mi" style="font-size:18px">close</span></button>`;

  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("show"));

  toast.querySelector(".toast-close").onclick = () => {
    toast.classList.remove("show");
    toast.classList.add("hide");
    setTimeout(() => toast.remove(), 400);
  };

  toast.querySelector('[data-action="download"]').onclick = () => {
    window.open(downloadUrl, "_blank");
    showNotification("下载已开始，安装后请重启应用", "success");
    toast.querySelector(".toast-close").click();
  };

  toast.querySelector('[data-action="github"]').onclick = () => {
    window.open(release.html_url, "_blank");
  };

  toast.querySelector('[data-action="dismiss"]').onclick = () => {
    localStorage.setItem("loarchive_update_skip", Date.now().toString());
    toast.querySelector(".toast-close").click();
  };
}

// 应用启动时检查更新

/* 应用启动后延迟检查更新（与原行为一致：24 小时内忽略过则跳过） */
export function initUpdateCheck() {
  setTimeout(() => {
    const skipTime = localStorage.getItem("loarchive_update_skip");
    if (!skipTime || Date.now() - parseInt(skipTime) > 86400000) {
      checkForUpdates(true);
    }
  }, 3000);
}
