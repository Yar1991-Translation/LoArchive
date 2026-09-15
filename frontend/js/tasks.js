import { API_BASE } from "./api.js";
import { AppState } from "./state.js";
import { escapeHtml, showNotification } from "./ui.js";
import { startTaskEventStream } from "./sse.js";

export async function startLstTask() {
  const url = document.getElementById("lstUrl").value.trim();
  if (!url) return showNotification("请输入链接地址", "error");
  await startTask("like_share_tag", {
    url,
    mode: AppState.currentMode,
    save_mode: {
      article: document.getElementById("saveArticle").checked ? 1 : 0,
      text: document.getElementById("saveText").checked ? 1 : 0,
      "long article": document.getElementById("saveLong").checked ? 1 : 0,
      img: document.getElementById("saveImg").checked ? 1 : 0,
    },
    start_time: document.getElementById("startTime").value,
    export_pdf: document.getElementById("lstExportPdf").checked,
  });
};
export async function startAuthorImgTask() {
  const url = document.getElementById("authorImgUrl").value.trim();
  if (!url) return showNotification("请输入作者主页链接", "error");
  await startTask("author_img", {
    author_url: url,
    start_time: document.getElementById("imgStartTime").value,
    end_time: document.getElementById("imgEndTime").value,
  });
};
export async function startAuthorTxtTask() {
  const url = document.getElementById("authorTxtUrl").value.trim();
  if (!url) return showNotification("请输入作者主页链接", "error");
  await startTask("author_txt", { author_url: url });
};
export async function startSingleTask() {
  const urls = document
    .getElementById("singleUrls")
    .value.split("\n")
    .map((u) => u.trim())
    .filter((u) => u);
  if (!urls.length) return showNotification("请输入至少一个链接", "error");
  const type =
    AppState.currentSingleMode === "img" ? "single_img" : "single_txt";
  await startTask(type, { urls });
};
export async function startAo3Task() {
  const urls = document
    .getElementById("ao3Urls")
    .value.split("\n")
    .map((u) => u.trim())
    .filter((u) => u);
  if (!urls.length) return showNotification("请输入至少一个 AO3 链接", "error");
  await startTask("ao3", {
    urls,
    mode: AppState.currentAo3Mode,
    download_chapters: document.getElementById("ao3DownloadChapters").checked,
    save_metadata: document.getElementById("ao3SaveMetadata").checked,
    export_pdf: document.getElementById("ao3ExportPdf").checked,
    export_epub: document.getElementById("ao3ExportEpub").checked,
    max_pages: parseInt(document.getElementById("ao3MaxPages").value) || 5,
  });
};
export async function startTask(type, params) {
  try {
    const res = await fetch(API_BASE + "/api/task/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, params }),
    });
    const ct = res.headers.get("content-type");
    if (!ct || !ct.includes("application/json")) {
      throw new Error("后端服务未启动");
    }
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    if (data.success) {
      AppState.isRunning = true;
      updateRunningState(true);
      showProgress(true);
      startTaskEvents();
      showNotification("任务已启动", "success");
    } else {
      showNotification(data.message, "error");
    }
  } catch (e) {
    showNotification("启动失败: " + e.message, "error");
  }
}
export function showProgress(show) {
  const section = document.getElementById("progressSection");
  if (section) section.classList.toggle("active", show);
}
export function updateRunningState(running) {
  const dot = document.getElementById("statusDot");
  const label = document.getElementById("statusLabel");
  if (dot && label) {
    if (running) {
      dot.classList.add("running");
      label.textContent = "运行中";
    } else {
      dot.classList.remove("running");
      label.textContent = "就绪";
    }
  }
}
export function startPolling() {
  if (AppState.pollInterval) clearInterval(AppState.pollInterval);
  AppState.pollInterval = setInterval(async () => {
    try {
      const res = await fetch(API_BASE + "/api/task/status");
      const ct = res.headers.get("content-type");
      if (!ct || !ct.includes("application/json")) return;
      const data = await res.json();
      const progressFill = document.getElementById("progressFill");
      const progressPercent = document.getElementById("progressPercent");
      const progressMessage = document.getElementById("progressMessage");
      if (progressFill) progressFill.style.width = data.progress + "%";
      if (progressPercent) progressPercent.textContent = data.progress + "%";
      if (progressMessage) progressMessage.textContent = data.message;
      const logContent = document.getElementById("logContent");
      if (logContent) {
        logContent.innerHTML = data.logs
          .map((log) => `<div class="log-line">${escapeHtml(log)}</div>`)
          .join("");
        logContent.scrollTop = logContent.scrollHeight;
      }
      if (!data.running && data.progress >= 100) {
        clearInterval(AppState.pollInterval);
        AppState.isRunning = false;
        updateRunningState(false);
        showNotification("任务完成！", "success");
      }
    } catch (e) {
      console.error("状态获取失败:", e);
    }
  }, 500);
}

/* ========== 任务事件：SSE 实时推送，失败时回退轮询 ========== */
export function startTaskEvents() {
  startTaskEventStream({
    // 快照是权威状态：短任务可能在订阅建立前就结束，done 事件会错过，
    // 因此这里也要按「已结束」收尾（与轮询回退的判定条件保持一致）。
    onSnapshot: (data) => {
      renderStatus(data);
      if (!data.running && data.progress >= 100) finishTask();
    },
    onLog: ({ line, message }) => {
      appendLogLine(line);
      setProgressMessage(message);
    },
    onProgress: ({ progress }) => setProgressPercent(progress),
    onDone: (data) => {
      // done 事件携带最终状态（进度 100 / 最终消息 / 完整日志），先渲染再收尾
      if (data) renderStatus(data);
      finishTask();
    },
    onFallback: () => startPolling(),
  });
}

function setProgressPercent(progress) {
  const progressFill = document.getElementById("progressFill");
  const progressPercent = document.getElementById("progressPercent");
  if (progressFill) progressFill.style.width = progress + "%";
  if (progressPercent) progressPercent.textContent = progress + "%";
}

function setProgressMessage(message) {
  const progressMessage = document.getElementById("progressMessage");
  if (progressMessage) progressMessage.textContent = message;
}

function appendLogLine(line) {
  const logContent = document.getElementById("logContent");
  if (!logContent) return;
  const div = document.createElement("div");
  div.className = "log-line";
  div.textContent = line;
  logContent.appendChild(div);
  // 与后端一致，最多保留 200 行日志
  while (logContent.children.length > 200) {
    logContent.removeChild(logContent.firstChild);
  }
  logContent.scrollTop = logContent.scrollHeight;
}

function renderStatus(data) {
  setProgressPercent(data.progress);
  setProgressMessage(data.message);
  const logContent = document.getElementById("logContent");
  if (logContent) {
    logContent.innerHTML = data.logs
      .map((log) => `<div class="log-line">${escapeHtml(log)}</div>`)
      .join("");
    logContent.scrollTop = logContent.scrollHeight;
  }
}

function finishTask() {
  AppState.isRunning = false;
  updateRunningState(false);
  showNotification("任务完成！", "success");
}
